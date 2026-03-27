"""Funcoes para gerar e comparar a primeira chave de ligacao."""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from typing import Any, Iterable

from config.comparacao_estados import CAMPOS_CHAVE_LIGACAO, VERSAO_CHAVE_LIGACAO
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


def gerar_chave_ligacao_valores(
    valores: dict[str, Any],
    campos: Iterable[str] = CAMPOS_CHAVE_LIGACAO,
) -> str:
    """Gera a chave de ligacao a partir de um conjunto de campos.

    A chave e um hash curto e estavel da combinacao normalizada dos campos.
    Isto evita guardar textos demasiado longos e permite evoluir a formula
    no futuro mantendo um prefixo de versao.
    """
    componentes: list[str] = []

    for campo in campos:
        valor_normalizado = normalizar_valor_para_comparacao(campo, valores.get(campo))
        if isinstance(valor_normalizado, float):
            texto_valor = f"{valor_normalizado:.3f}"
        else:
            texto_valor = str(valor_normalizado or "")

        componentes.append(f"{campo}={texto_valor}")

    base_chave = "|".join(componentes)
    if not base_chave.replace("|", "").replace("=", ""):
        return ""

    hash_sha1 = hashlib.sha1(base_chave.encode("utf-8")).hexdigest()
    return f"{VERSAO_CHAVE_LIGACAO}_{hash_sha1}"


def gerar_chave_ligacao_linha(linha: Any) -> str:
    """Gera a chave de ligacao a partir de um objeto com atributos da linha."""
    valores = {campo: getattr(linha, campo, None) for campo in CAMPOS_CHAVE_LIGACAO}
    return gerar_chave_ligacao_valores(valores)
