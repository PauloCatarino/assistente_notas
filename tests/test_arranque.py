"""Testes simples para validar a base do projeto."""

from __future__ import annotations

import unittest

from parsers.extrair_tokens_mpr import ExtratorTokensMPR
from utils.helpers import normalizar_nome_coluna, normalizar_texto_chave


class TestHelpers(unittest.TestCase):
    """Valida pequenos comportamentos utilitários."""

    def test_normalizar_nome_coluna(self) -> None:
        """Deve transformar cabeçalhos em nomes previsíveis."""
        self.assertEqual(normalizar_nome_coluna("Nº Linha", 1), "n_linha")
        self.assertEqual(normalizar_nome_coluna(None, 2), "coluna_2")

    def test_normalizar_texto_chave(self) -> None:
        """Deve lidar com sinais e pontuação que aparecem nos Excel."""
        self.assertEqual(normalizar_texto_chave("Comp."), "comp")
        self.assertEqual(normalizar_texto_chave("Esp.Mat"), "esp_mat")
        self.assertEqual(normalizar_texto_chave("+comp"), "mais_comp")


class TestExtratorTokens(unittest.TestCase):
    """Valida a extração inicial de tokens a partir de texto `.mpr`."""

    def test_extrair_tokens_de_texto(self) -> None:
        """Deve encontrar tokens relevantes e contar ocorrências."""
        texto = """
        CNC_PUX_J_FRESADO_ORLA
        PRF_CORTE_sem_CAM
        FRESAR_RECORTES_VARADO
        CNC_PUX_J_FRESADO_ORLA
        """

        extrator = ExtratorTokensMPR()
        tokens = extrator.extrair_tokens_de_texto(texto)
        mapa = {token.token: token.ocorrencias for token in tokens}

        self.assertEqual(mapa["CNC_PUX_J_FRESADO_ORLA"], 2)
        self.assertIn("PRF_CORTE_sem_CAM", mapa)
        self.assertIn("FRESAR_RECORTES_VARADO", mapa)


if __name__ == "__main__":
    unittest.main()
