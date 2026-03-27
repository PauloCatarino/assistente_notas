"""Testes focados na leitura e normalização das folhas Excel."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from importers.importar_excel_cutrite import ImportadorFolhasExcel


class TestImportadorFolhasExcel(unittest.TestCase):
    """Valida a leitura das duas folhas com linhas de cabeçalho diferentes."""

    def test_ler_folhas_configuradas(self) -> None:
        """Deve encontrar os cabeçalhos corretos e mapear as linhas úteis."""
        with tempfile.TemporaryDirectory() as pasta_temporaria:
            caminho_excel = Path(pasta_temporaria) / "obra_teste.xlsx"
            self._criar_workbook_teste(caminho_excel)

            importador = ImportadorFolhasExcel()
            resultados = importador.ler_folhas_configuradas(caminho_excel)

            self.assertEqual(len(resultados), 2)

            resultado_original = next(
                resultado for resultado in resultados if resultado.nome_folha_esperada == "LISTA_ORDENADA"
            )
            resultado_transformado = next(
                resultado for resultado in resultados if resultado.nome_folha_esperada == "LISTAGEM_CUT_RITE"
            )

            self.assertEqual(resultado_original.linha_cabecalho, 3)
            self.assertEqual(resultado_transformado.linha_cabecalho, 2)
            self.assertEqual(resultado_original.total_linhas(), 1)
            self.assertEqual(resultado_transformado.total_linhas(), 1)
            self.assertEqual(resultado_original.linhas[0].descricao, "Costa")
            self.assertEqual(resultado_transformado.linhas[0].id_linha_excel, "1")

    @staticmethod
    def _criar_workbook_teste(caminho_excel: Path) -> None:
        """Cria um Excel simples que replica o padrão do ficheiro real."""
        workbook = Workbook()

        folha_original = workbook.active
        folha_original.title = "LISTA_ORDENADA"
        folha_original.append([None] * 18)
        folha_original.append([None] * 18)
        folha_original.append(
            [
                None,
                "Descricao",
                "Material",
                "Comp.",
                "Larg.",
                "Esp",
                "Qt.",
                "Veio",
                "Orla ESQ",
                "Orla DIR",
                "Orla CIMA",
                "Orla BAIXO",
                "CNC_1",
                "CNC_2",
                "Enc.",
                "Cliente",
                "Artigo",
                "Notas",
            ]
        )
        folha_original.append(
            [
                None,
                "Costa",
                "Material A",
                1000,
                500,
                19,
                2,
                "N",
                "PVC_A",
                "PVC_B",
                "PVC_C",
                "PVC_D",
                "CNC_A",
                "CNC_B",
                "ENC_1",
                "Cliente X",
                "ART_01",
                "Nota teste",
            ]
        )

        folha_transformada = workbook.create_sheet("LISTAGEM_CUT_RITE")
        folha_transformada.append([None] * 26)
        folha_transformada.append(
            [
                "Descricao",
                "Material",
                "Comp",
                "Larg",
                "Qt",
                "Veio",
                "Orla",
                "Cliente",
                "Ref_Cliente",
                "Processo",
                "Artigo",
                "Notas",
                "Esp",
                "Grafico Orlas",
                "Orla ESQ",
                "Orla DIR",
                "Orla CIMA",
                "Orla BAIXO",
                "ID",
                "CNC_1",
                "CNC_2",
                "+comp",
                "+Larg",
                "Esp.Mat",
                "Esp.Final",
                "Tipo_Lacagem",
            ]
        )
        folha_transformada.append(
            [
                "Costa",
                "Material B",
                1200,
                600,
                1,
                "S",
                None,
                "Cliente Y",
                "2504027",
                "0560_01_26",
                "ART_02",
                "Nota B",
                18,
                None,
                "PVC_A",
                "PVC_B",
                "PVC_C",
                "PVC_D",
                1,
                "CNC_X",
                "CNC_Y",
                None,
                None,
                18,
                18,
                None,
            ]
        )

        workbook.save(caminho_excel)
        workbook.close()
