"""Testes para chave_ligacao e comparacao entre estados."""

from __future__ import annotations

import unittest

from models.schemas import LinhaObra
from services.servico_comparacao_estados import ServicoComparacaoEstados


class TestChaveLigacao(unittest.TestCase):
    """Valida a primeira versao da chave de ligacao."""

    def test_mesma_chave_para_valores_equivalentes(self) -> None:
        """Deve gerar a mesma chave para variacoes simples de formato."""
        linha_original = LinhaObra(
            obra_id=1,
            estado_origem="ORIGINAL_IMOS",
            nome_folha_origem="LISTA_ORDENADA",
            linha_excel=10,
            descricao="Costa",
            material="Material A",
            comp=1000,
            larg=500.0,
            qt=2,
            artigo="ART_01",
            veio="N",
        )

        linha_transformada = LinhaObra(
            obra_id=1,
            estado_origem="TRANSFORMADO_AUTOMATION",
            nome_folha_origem="LISTAGEM_CUT_RITE",
            linha_excel=8,
            descricao=" costa ",
            material="material a",
            comp=1000.0001,
            larg=500,
            qt=2.0,
            artigo="art_01",
            veio="n",
        )

        self.assertEqual(linha_original.chave_ligacao, linha_transformada.chave_ligacao)


class TestComparacaoEstados(unittest.TestCase):
    """Valida a primeira comparacao estruturada."""

    def test_comparar_linhas_em_memoria(self) -> None:
        """Deve identificar alteracoes e ausencias simples."""
        servico = ServicoComparacaoEstados()

        linha_original = LinhaObra(
            id=1,
            obra_id=1,
            estado_origem="ORIGINAL_IMOS",
            nome_folha_origem="LISTA_ORDENADA",
            linha_excel=10,
            descricao="Costa",
            material="Material A",
            comp=1000,
            larg=500,
            qt=2,
            artigo="ART_01",
            veio="N",
            notas="Sem nota",
        )

        linha_transformada = LinhaObra(
            id=2,
            obra_id=1,
            estado_origem="TRANSFORMADO_AUTOMATION",
            nome_folha_origem="LISTAGEM_CUT_RITE",
            linha_excel=8,
            descricao="Costa",
            material="Material A",
            comp=1000,
            larg=500,
            qt=2,
            artigo="ART_01",
            veio="N",
            notas="Nota alterada",
        )

        linha_sem_par = LinhaObra(
            id=3,
            obra_id=1,
            estado_origem="ORIGINAL_IMOS",
            nome_folha_origem="LISTA_ORDENADA",
            linha_excel=12,
            descricao="Frente",
            material="Material B",
            comp=900,
            larg=450,
            qt=1,
            artigo="ART_02",
            veio="S",
        )

        resumo = servico.comparar_linhas_em_memoria(
            obra_id=1,
            linhas_base=[linha_original, linha_sem_par],
            linhas_alvo=[linha_transformada],
            estado_base="ORIGINAL_IMOS",
            estado_alvo="TRANSFORMADO_AUTOMATION",
        )

        self.assertEqual(resumo.total_linhas_base, 2)
        self.assertEqual(resumo.total_linhas_alvo, 1)
        self.assertEqual(resumo.total_chaves_ligadas, 1)
        self.assertEqual(resumo.total_pares_ligados, 1)
        self.assertEqual(resumo.total_diferencas, 2)

        tipos = {diferenca.tipo_diferenca for diferenca in resumo.diferencas}
        campos = {diferenca.campo for diferenca in resumo.diferencas}

        self.assertIn("VALOR_ALTERADO", tipos)
        self.assertIn("AUSENTE_NO_TRANSFORMADO", tipos)
        self.assertIn("notas", campos)


if __name__ == "__main__":
    unittest.main()
