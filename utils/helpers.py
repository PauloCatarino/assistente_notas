"""Funcoes auxiliares simples e reutilizaveis."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


def garantir_pastas(caminhos: Iterable[Path]) -> None:
    """Cria as pastas indicadas se ainda nao existirem."""
    for caminho in caminhos:
        Path(caminho).mkdir(parents=True, exist_ok=True)


def normalizar_texto_chave(valor: object) -> str:
    """Normaliza texto para uma chave previsivel.

    Esta funcao e usada para tornar comparaveis cabecalhos Excel
    com pequenas diferencas de escrita, por exemplo:
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

    # Alguns cabecalhos podem trazer simbolos como `o` sobrescrito.
    # Aqui removemo-los antes da normalizacao para evitar ruido.
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
    """Mantem compatibilidade com a funcao usada na fase inicial."""
    chave = normalizar_texto_chave(valor)
    return chave or f"coluna_{indice}"


def limpar_texto(valor: object) -> str:
    """Converte um valor para texto simples, removendo espacos laterais."""
    if valor is None:
        return ""

    return str(valor).strip()


def converter_para_numero(valor: object) -> float | None:
    """Converte um valor para numero decimal simples quando possivel."""
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


def calcular_hash_ficheiro(caminho_ficheiro: Path, tamanho_bloco: int = 65536) -> str:
    """Calcula um hash SHA-256 do ficheiro.

    O hash e usado como identificador forte para bloquear reimportacoes
    do mesmo ficheiro com o mesmo conteudo.
    """
    hash_sha256 = hashlib.sha256()

    with Path(caminho_ficheiro).open("rb") as ficheiro:
        for bloco in iter(lambda: ficheiro.read(tamanho_bloco), b""):
            hash_sha256.update(bloco)

    return hash_sha256.hexdigest()


def obter_metadados_ficheiro(caminho_ficheiro: Path) -> tuple[str, int, datetime]:
    """Devolve nome, tamanho e data de modificacao do ficheiro."""
    caminho_ficheiro = Path(caminho_ficheiro)
    estatisticas = caminho_ficheiro.stat()

    return (
        caminho_ficheiro.name,
        int(estatisticas.st_size),
        datetime.fromtimestamp(estatisticas.st_mtime),
    )


def timestamp_atual() -> str:
    """Devolve o instante atual em formato ISO simples."""
    return datetime.now().isoformat(timespec="seconds")


def escrever_json_linha(caminho_ficheiro: Path, dados: dict[str, Any]) -> None:
    """Escreve uma linha JSON num ficheiro de log local."""
    caminho_ficheiro = Path(caminho_ficheiro)
    caminho_ficheiro.parent.mkdir(parents=True, exist_ok=True)

    with caminho_ficheiro.open("a", encoding="utf-8") as ficheiro:
        ficheiro.write(json.dumps(dados, ensure_ascii=False) + "\n")
