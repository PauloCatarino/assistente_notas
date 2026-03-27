"""Funções auxiliares simples e reutilizáveis."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


def garantir_pastas(caminhos: Iterable[Path]) -> None:
    """Cria as pastas indicadas se ainda não existirem."""
    for caminho in caminhos:
        Path(caminho).mkdir(parents=True, exist_ok=True)


def normalizar_texto_chave(valor: object) -> str:
    """Normaliza texto para uma chave previsível.

    Esta função é usada para tornar comparáveis cabeçalhos Excel
    com pequenas diferenças de escrita, por exemplo:
    - `Comp.` -> `comp`
    - `Esp.Mat` -> `esp_mat`
    - `Ref_Cliente` -> `ref_cliente`
    - `+comp` -> `mais_comp`
    """
    if valor is None:
        return ""

    texto = str(valor).strip().replace("\n", " ")
    if not texto:
        return ""

    # Alguns cabeçalhos podem trazer símbolos como `º` e `ª`.
    # Aqui removemo-los antes da normalização para evitar ruído como `no_linha`.
    texto = texto.replace("º", "").replace("ª", "")
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = texto.replace("+", " mais ")
    texto = texto.replace("&", " e ")
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9_]+", "_", texto)
    texto = re.sub(r"_+", "_", texto)

    return texto.strip("_")


def normalizar_nome_coluna(valor: object, indice: int) -> str:
    """Mantém compatibilidade com a função usada na fase inicial."""
    chave = normalizar_texto_chave(valor)
    return chave or f"coluna_{indice}"


def limpar_texto(valor: object) -> str:
    """Converte um valor para texto simples, removendo espaços laterais."""
    if valor is None:
        return ""

    return str(valor).strip()


def converter_para_numero(valor: object) -> float | None:
    """Converte um valor para número decimal simples quando possível."""
    if valor is None or valor == "":
        return None

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()
    if not texto:
        return None

    texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return None


def timestamp_atual() -> str:
    """Devolve o instante atual em formato ISO simples."""
    return datetime.now().isoformat(timespec="seconds")


def escrever_json_linha(caminho_ficheiro: Path, dados: dict[str, Any]) -> None:
    """Escreve uma linha JSON num ficheiro de log local."""
    caminho_ficheiro = Path(caminho_ficheiro)
    caminho_ficheiro.parent.mkdir(parents=True, exist_ok=True)

    with caminho_ficheiro.open("a", encoding="utf-8") as ficheiro:
        ficheiro.write(json.dumps(dados, ensure_ascii=False) + "\n")
