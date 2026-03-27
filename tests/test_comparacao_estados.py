"""Testes para chave_ligacao v2 e comparacao entre estados."""

from __future__ import annotations

import unittest

from models.schemas import LinhaObra
from services.servico_comparacao_estados import ServicoComparacaoEstados


class TestChaveLigacaoV2(unittest.TestCase):
    """Valida a segunda versao da estrategia de ligacao."""

    def test_chave_tolerante_mantem_grupo_mesmo_com_medidas_diferentes(self) -> None:
        """A chave v2 deve agrupar candidatos equivalentes pelos campos mais estaveis."""
        linha_original = LinhaObra(
            obra_id=1,
            estado_origem="ORIGINAL_IMOS",
            nome_folha_origem="LISTA_ORDENADA",
            linha_excel=10,
            descricao="Costa lateral",
            material="MDF Branco",
            comp=1000,
            larg=500,
            qt=2,
            artigo="ART_01",
            veio="N",
        )

        linha_transformada = LinhaObra(
            obra_id=1,
            estado_origem="TRANSFORMADO_AUTOMATION",
            nome_folha_origem="LISTAGEM_CUT_RITE",
            linha_excel=8,
            descricao="  costa lateral ",
            material="mdf branco",
            comp=1005,
            larg=498,
            qt=3,
            artigo="art_01",
            veio="n",
        )

        self.assertEqual(linha_original.chave_ligacao, linha_transformada.chave_ligacao)
        self.assertNotEqual(
            linha_original.gerar_assinatura_forte(),
            linha_transformada.gerar_assinatura_forte(),
        )


class TestComparacaoEstadosV2(unittest.TestCase):
    """Valida a ligacao tolerante e a classificacao das diferencas."""

    def test_correspondencia_tolerante_com_medidas_trocadas(self) -> None:
        """Deve ligar linhas equivalentes mesmo quando comp e larg surgem trocados."""
        servico = ServicoComparacaoEstados()

        linha_original = LinhaObra(
            id=1,
            obra_id=1,
            estado_origem="ORIGINAL_IMOS",
            nome_folha_origem="LISTA_ORDENADA",
            linha_excel=10,
            descricao="Prateleira",
            material="MDF Branco",
            comp=1000,
            larg=500,
            qt=1,
            artigo="PRAT_01",
            veio="N",
            notas="",
        )

        linha_transformada = LinhaObra(
            id=2,
            obra_id=1,
            estado_origem="TRANSFORMADO_AUTOMATION",
            nome_folha_origem="LISTAGEM_CUT_RITE",
            linha_excel=7,
            descricao="prateleira",
            material="mdf branco",
            comp=500,
            larg=1000,
            qt=1,
            artigo="prat_01",
            veio="n",
            notas="Nota do automation",
        )

        resumo = servico.comparar_linhas_em_memoria(
            obra_id=1,
            linhas_base=[linha_original],
            linhas_alvo=[linha_transformada],
            estado_base="ORIGINAL_IMOS",
            estado_alvo="TRANSFORMADO_AUTOMATION",
        )

        self.assertEqual(resumo.total_chaves_ligadas, 1)
        self.assertEqual(resumo.total_pares_ligados, 1)
        self.assertEqual(resumo.total_linhas_sem_correspondencia, 0)

        par = resumo.pares_correspondencia[0]
        self.assertEqual(par.nivel_correspondencia, "TOLERANTE")
        self.assertGreaterEqual(par.score_correspondencia, 65)

        tipos = {diferenca.tipo_diferenca for diferenca in resumo.diferencas}
        self.assertIn("MEDIDA_ALTERADA", tipos)
        self.assertIn("NOTA_ADICIONADA", tipos)

    def test_classifica_linha_sem_par(self) -> None:
        """Deve marcar claramente uma linha sem correspondencia."""
        servico = ServicoComparacaoEstados()

        linha_original = LinhaObra(
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
            linhas_base=[linha_original],
            linhas_alvo=[],
            estado_base="ORIGINAL_IMOS",
            estado_alvo="TRANSFORMADO_AUTOMATION",
        )

        self.assertEqual(resumo.total_pares_ligados, 0)
        self.assertEqual(resumo.total_sem_correspondencia_base, 1)
        self.assertEqual(resumo.total_sem_correspondencia_alvo, 0)
        self.assertEqual(resumo.total_linhas_sem_correspondencia, 1)
        self.assertEqual(resumo.total_diferencas, 1)
        self.assertEqual(resumo.diferencas[0].tipo_diferenca, "LINHA_SEM_PAR")
        self.assertEqual(resumo.diferencas[0].nivel_correspondencia, "SEM_PAR")


if __name__ == "__main__":
    unittest.main()
