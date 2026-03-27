"""Funcoes para gerar chaves e score de correspondencia entre estados."""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from typing import Any, Iterable

from config.comparacao_estados import (
    CAMPOS_CHAVE_FORTE,
    CAMPOS_CHAVE_LIGACAO,
    LIMIAR_SCORE_CORRESPONDENCIA_TOLERANTE,
    PESOS_SCORE_CORRESPONDENCIA,
    VERSAO_CHAVE_LIGACAO,
)
from utils.helpers import converter_para_numero


CAMPOS_NUMERICOS_COMPARACAO = {"comp", "larg", "qt", "esp", "esp_mat", "esp_final"}


def normalizar_texto_para_comparacao(valor: object) -> str:
    """Normaliza texto de forma leve para comparacao funcional."""
    if valor is None:
        return ""

    texto = str(valor).strip().lower()
    if not texto:
        return ""

    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def normalizar_numero_para_comparacao(valor: object, casas_decimais: int = 3) -> float | None:
    """Normaliza numeros para evitar diferencas irrelevantes de formato."""
    numero = converter_para_numero(valor)
    if numero is None:
        return None

    if math.isnan(numero):
        return None

    return round(float(numero), casas_decimais)


def normalizar_valor_para_comparacao(campo: str, valor: object) -> str | float | None:
    """Normaliza um valor conforme o tipo do campo antes de comparar."""
    if campo in CAMPOS_NUMERICOS_COMPARACAO:
        return normalizar_numero_para_comparacao(valor)

    texto = normalizar_texto_para_comparacao(valor)
    return texto or None


def valor_para_texto_legivel(valor: object) -> str | None:
    """Converte um valor para texto legivel para logs e base de dados."""
    if valor is None:
        return None

    if isinstance(valor, float):
        return f"{valor:.3f}".rstrip("0").rstrip(".")

    texto = str(valor).strip()
    return texto or None


def gerar_hash_componentes(componentes: list[str]) -> str:
    """Cria um hash curto e estavel a partir de componentes normalizados."""
    base_chave = "|".join(componentes)
    if not base_chave.replace("|", "").replace("=", ""):
        return ""

    hash_sha1 = hashlib.sha1(base_chave.encode("utf-8")).hexdigest()
    return f"{VERSAO_CHAVE_LIGACAO}_{hash_sha1}"


def gerar_chave_ligacao_valores(
    valores: dict[str, Any],
    campos: Iterable[str] = CAMPOS_CHAVE_LIGACAO,
) -> str:
    """Gera a chave tolerante v2.

    A v2 usa apenas os campos textuais mais estaveis entre estados.
    Isso torna a chave melhor para agrupar candidatos, enquanto
    `comp`, `larg` e `qt` passam a influenciar o score de semelhanca.
    """
    componentes: list[str] = []

    for campo in campos:
        valor_normalizado = normalizar_valor_para_comparacao(campo, valores.get(campo))
        componentes.append(f"{campo}={str(valor_normalizado or '')}")

    return gerar_hash_componentes(componentes)


def gerar_assinatura_forte_valores(
    valores: dict[str, Any],
    campos: Iterable[str] = CAMPOS_CHAVE_FORTE,
) -> str:
    """Gera a assinatura forte para ligacao direta.

    Quando esta assinatura coincide em ambos os estados, a
    correspondencia e considerada forte.
    """
    componentes: list[str] = []

    for campo in campos:
        valor_normalizado = normalizar_valor_para_comparacao(campo, valores.get(campo))
        if isinstance(valor_normalizado, float):
            texto_valor = f"{valor_normalizado:.3f}"
        else:
            texto_valor = str(valor_normalizado or "")
        componentes.append(f"{campo}={texto_valor}")

    return gerar_hash_componentes(componentes)


def gerar_chave_ligacao_linha(linha: Any) -> str:
    """Gera a chave tolerante v2 a partir de um objeto de linha."""
    valores = {campo: getattr(linha, campo, None) for campo in CAMPOS_CHAVE_LIGACAO}
    return gerar_chave_ligacao_valores(valores)


def gerar_assinatura_forte_linha(linha: Any) -> str:
    """Gera a assinatura forte da linha."""
    valores = {campo: getattr(linha, campo, None) for campo in CAMPOS_CHAVE_FORTE}
    return gerar_assinatura_forte_valores(valores)


def score_texto_exato(valor_a: object, valor_b: object, peso: int) -> int:
    """Devolve o peso completo quando o texto normalizado coincide."""
    if normalizar_texto_para_comparacao(valor_a) and normalizar_texto_para_comparacao(valor_a) == normalizar_texto_para_comparacao(valor_b):
        return peso
    return 0


def score_numero_com_tolerancia(
    valor_a: object,
    valor_b: object,
    tolerancia_forte: float,
    tolerancia_media: float,
    peso: int,
) -> int:
    """Calcula score parcial para um campo numerico com tolerancias simples."""
    numero_a = normalizar_numero_para_comparacao(valor_a)
    numero_b = normalizar_numero_para_comparacao(valor_b)

    if numero_a is None or numero_b is None:
        return 0

    diferenca = abs(numero_a - numero_b)
    if diferenca <= tolerancia_forte:
        return peso
    if diferenca <= tolerancia_media:
        return int(round(peso * 0.6))
    return 0


def score_dimensoes(linha_a: Any, linha_b: Any, peso_total: int) -> int:
    """Calcula score para `comp` e `larg`.

    Esta funcao considera dois cenarios:
    - comparacao direta `comp-comp` e `larg-larg`
    - comparacao cruzada `comp-larg` e `larg-comp`

    O segundo caso ajuda quando um processo posterior roda a peca.
    """
    metade_peso = int(peso_total / 2)

    score_direto = score_numero_com_tolerancia(linha_a.comp, linha_b.comp, 1.0, 20.0, metade_peso)
    score_direto += score_numero_com_tolerancia(linha_a.larg, linha_b.larg, 1.0, 20.0, metade_peso)

    score_cruzado = score_numero_com_tolerancia(linha_a.comp, linha_b.larg, 1.0, 20.0, metade_peso)
    score_cruzado += score_numero_com_tolerancia(linha_a.larg, linha_b.comp, 1.0, 20.0, metade_peso)

    return max(score_direto, score_cruzado)


def calcular_score_correspondencia(linha_a: Any, linha_b: Any) -> int:
    """Calcula um score simples de semelhanca entre duas linhas.

    Esta v2 privilegia clareza:
    - texto principal com peso alto
    - quantidade com peso medio
    - medidas com tolerancia e suporte a troca comp/larg
    """
    score = 0

    score += score_texto_exato(linha_a.descricao, linha_b.descricao, PESOS_SCORE_CORRESPONDENCIA["descricao"])
    score += score_texto_exato(linha_a.material, linha_b.material, PESOS_SCORE_CORRESPONDENCIA["material"])
    score += score_texto_exato(linha_a.artigo, linha_b.artigo, PESOS_SCORE_CORRESPONDENCIA["artigo"])
    score += score_texto_exato(linha_a.veio, linha_b.veio, PESOS_SCORE_CORRESPONDENCIA["veio"])
    score += score_numero_com_tolerancia(
        linha_a.qt,
        linha_b.qt,
        tolerancia_forte=0.01,
        tolerancia_media=1.0,
        peso=PESOS_SCORE_CORRESPONDENCIA["qt"],
    )
    score += score_dimensoes(linha_a, linha_b, PESOS_SCORE_CORRESPONDENCIA["dimensoes"])

    return min(score, 100)


def classificar_nivel_correspondencia(score_correspondencia: int, assinatura_forte_igual: bool) -> str:
    """Classifica a correspondencia em niveis simples."""
    if assinatura_forte_igual:
        return "FORTE"

    if score_correspondencia >= LIMIAR_SCORE_CORRESPONDENCIA_TOLERANTE:
        return "TOLERANTE"

    return "SEM_PAR"


def aceitar_correspondencia_tolerante(score_correspondencia: int) -> bool:
    """Indica se um score tolerante deve ser aceite."""
    return score_correspondencia >= LIMIAR_SCORE_CORRESPONDENCIA_TOLERANTE
