"""Extração simples de tokens úteis a partir de ficheiros `.mpr`."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from models.schemas import TokenCNC
from parsers.ler_mpr import LeitorMPR


class ExtratorTokensMPR:
    """Extrai tokens em maiúsculas que podem ser úteis para futuras sugestões.

    A regra inicial é intencionalmente simples:
    procurar sequências com letras, números e underscore.

    Exemplos esperados:
    - CNC_PUX_J_FRESADO_ORLA
    - PRF_CORTE_sem_CAM
    - FRESAR_RECORTES_VARADO

    Nota:
    a expressão regular abaixo privilegia clareza em vez de sofisticação.
    Poderá ser refinada quando existirem mais exemplos reais.
    """

    PADRAO_TOKEN = re.compile(r"\b[A-Za-z0-9_]{3,}\b")

    def __init__(self, leitor_mpr: LeitorMPR | None = None) -> None:
        """Permite reutilizar um leitor `.mpr` já existente."""
        self.leitor_mpr = leitor_mpr or LeitorMPR()

    def extrair_tokens_de_texto(self, texto: str, origem: str = "") -> list[TokenCNC]:
        """Extrai tokens de um bloco de texto e conta ocorrências."""
        candidatos = self.PADRAO_TOKEN.findall(texto)

        # Filtramos tokens sem letras para evitar ruído como números isolados.
        tokens_validos = [
            token
            for token in candidatos
            if "_" in token or any(caractere.isalpha() for caractere in token)
        ]

        contagem = Counter(tokens_validos)
        resultado: list[TokenCNC] = []

        for token, ocorrencias in sorted(contagem.items()):
            resultado.append(
                TokenCNC(
                    cnc_programa_id=None,
                    token=token,
                    ocorrencias=ocorrencias,
                    origem=origem,
                )
            )

        return resultado

    def extrair_tokens_de_ficheiro(self, caminho_ficheiro: Path) -> list[TokenCNC]:
        """Lê um ficheiro `.mpr` e devolve os tokens encontrados."""
        texto = self.leitor_mpr.ler_texto(caminho_ficheiro)
        return self.extrair_tokens_de_texto(texto=texto, origem=str(caminho_ficheiro))
