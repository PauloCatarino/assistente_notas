"""Testes para o parser do nome da obra e para o motor de sugestoes."""

from __future__ import annotations

import unittest
from pathlib import Path

from importers.importar_obras import ImportadorObras
from datetime import datetime

from models.schemas import FeedbackSugestaoNota, LinhaObra
from services.servico_sugestoes import ServicoSugestoes


class TestImportadorObras(unittest.TestCase):
    """Valida a interpretacao do nome do ficheiro da obra."""

    def test_interpretar_nome_ficheiro_obra_real(self) -> None:
        """Deve extrair as partes esperadas de um nome no formato real."""
        importador = ImportadorObras(Path("."))
        dados = importador._interpretar_nome_ficheiro("Lista_Material_0560_01_26_JF_VIVA")

        self.assertEqual(dados["nome_base"], "Lista_Material")
        self.assertEqual(dados["referencia_obra"], "0560_01_26_JF_VIVA")
        self.assertEqual(dados["num_encomenda_phc"], "0560")
        self.assertEqual(dados["versao_obra"], "01")
        self.assertEqual(dados["ano_obra"], "26")
        self.assertEqual(dados["cliente_codigo"], "JF_VIVA")


class TestServicoSugestoes(unittest.TestCase):
    """Valida a primeira heuristica de sugestoes."""

    def test_gera_sugestao_com_historico_semelhante(self) -> None:
        """Deve devolver a nota historica quando o padrao for forte o suficiente."""
        servico = ServicoSugestoes()

        linha_alvo = LinhaObra(
            obra_id=None,
            estado_origem="TRANSFORMADO_AUTOMATION",
            nome_folha_origem="LISTAGEM_CUT_RITE",
            linha_excel=12,
            descricao="Costa lateral",
            material="MDF Branco",
            artigo="ART_10",
            veio="N",
            esp=19,
            esp_mat=19,
            esp_final=19,
            orla_esq="ABS_1",
            orla_dir="ABS_1",
            orla_cima="",
            orla_baixo="",
            notas="",
        )

        historico = [
            LinhaObra(
                obra_id=1,
                estado_origem="TRANSFORMADO_AUTOMATION",
                nome_folha_origem="LISTAGEM_CUT_RITE",
                linha_excel=20,
                descricao="Costa lateral",
                material="MDF Branco",
                artigo="ART_10",
                veio="N",
                esp=19,
                esp_mat=19,
                esp_final=19,
                orla_esq="ABS_1",
                orla_dir="ABS_1",
                notas="Fresar puxador",
            ),
            LinhaObra(
                obra_id=2,
                estado_origem="TRANSFORMADO_AUTOMATION",
                nome_folha_origem="LISTAGEM_CUT_RITE",
                linha_excel=25,
                descricao="Costa lateral",
                material="MDF Branco",
                artigo="ART_10",
                veio="N",
                esp=19,
                esp_mat=19,
                esp_final=19,
                orla_esq="ABS_1",
                orla_dir="ABS_1",
                notas="Fresar puxador",
            ),
        ]

        sugestao = servico.gerar_sugestoes_para_linhas(obra_id=10, linhas_alvo=[linha_alvo], historico=historico)[0]

        self.assertEqual(sugestao.sugestao_1, "Fresar puxador")
        self.assertGreaterEqual(sugestao.score_1, 65)
        self.assertIn("linha(s) historica(s)", sugestao.justificacao)
        self.assertEqual(sugestao.obra_id, 10)

    def test_nao_gera_sugestao_sem_historico_forte(self) -> None:
        """Deve manter a sugestao vazia quando o historico nao for convincente."""
        servico = ServicoSugestoes()

        linha_alvo = LinhaObra(
            obra_id=None,
            estado_origem="TRANSFORMADO_AUTOMATION",
            nome_folha_origem="LISTAGEM_CUT_RITE",
            linha_excel=30,
            descricao="Fundo gaveta",
            material="Contraplacado",
            artigo="ART_X",
            veio="S",
            notas="",
        )

        historico = [
            LinhaObra(
                obra_id=1,
                estado_origem="TRANSFORMADO_AUTOMATION",
                nome_folha_origem="LISTAGEM_CUT_RITE",
                linha_excel=40,
                descricao="Lateral armario",
                material="MDF Branco",
                artigo="ART_Y",
                veio="N",
                notas="Nota historica",
            )
        ]

        sugestao = servico.gerar_sugestoes_para_linhas(obra_id=20, linhas_alvo=[linha_alvo], historico=historico)[0]

        self.assertEqual(sugestao.sugestao_1, "")
        self.assertEqual(sugestao.score_1, 0)
        self.assertIn("Sem historico suficiente", sugestao.justificacao)

    def test_normaliza_feedback_aceite_e_editado(self) -> None:
        """Deve classificar estados de feedback de forma previsivel."""
        servico = ServicoSugestoes()

        self.assertEqual(
            servico.normalizar_estado_feedback("aceite", "Nota A", ""),
            "ACEITE",
        )
        self.assertEqual(
            servico.normalizar_estado_feedback("", "Nota A", "Nota Final"),
            "EDITADA",
        )
        self.assertEqual(
            servico.normalizar_estado_feedback("não aceite", "Nota A", ""),
            "REJEITADA",
        )
        self.assertEqual(
            servico.normalizar_estado_feedback("aceite sugestao 2", "Nota A", "Nota B"),
            "EDITADA",
        )

    def test_feedback_hash_e_estavel_e_distingue_alteracoes(self) -> None:
        """O hash deve repetir para o mesmo feedback e mudar quando o conteudo muda."""
        servico = ServicoSugestoes()
        base = FeedbackSugestaoNota(
            obra_id=1,
            linha_excel=10,
            descricao="Costa",
            material="MDF",
            artigo="ART_1",
            notas_atual="",
            sugestao_1="Nota A",
            score_1=90,
            sugestao_2="",
            score_2=0,
            justificacao="Teste",
            validacao_utilizador="aceite",
            nota_final_utilizador="Nota A",
            data_feedback=datetime.now(),
        )

        hash_1 = servico.criar_feedback_hash(base)
        hash_2 = servico.criar_feedback_hash(base)
        self.assertEqual(hash_1, hash_2)

        alterado = FeedbackSugestaoNota(
            obra_id=1,
            linha_excel=10,
            descricao="Costa",
            material="MDF",
            artigo="ART_1",
            notas_atual="",
            sugestao_1="Nota A",
            score_1=90,
            sugestao_2="",
            score_2=0,
            justificacao="Teste",
            validacao_utilizador="rejeitada",
            nota_final_utilizador="",
            data_feedback=datetime.now(),
        )
        self.assertNotEqual(hash_1, servico.criar_feedback_hash(alterado))

    def test_contexto_recalibracao_penaliza_nota_rejeitada(self) -> None:
        """Feedback repetidamente rejeitado deve reduzir a confianca da nota."""
        servico = ServicoSugestoes()
        feedbacks = [
            FeedbackSugestaoNota(
                obra_id=1,
                linha_excel=10 + indice,
                descricao="Costa",
                material="MDF",
                artigo="ART_1",
                notas_atual="",
                sugestao_1="Nota Fraca",
                score_1=85,
                sugestao_2="",
                score_2=0,
                justificacao="Teste",
                validacao_utilizador="rejeitada",
                nota_final_utilizador="",
                data_feedback=datetime.now(),
            )
            for indice in range(3)
        ]

        contexto = servico.construir_contexto_recalibracao(feedbacks)
        ajuste, detalhe = servico._calcular_ajuste_recalibracao("Costa", "Nota Fraca", contexto)

        self.assertLess(ajuste, 0)
        self.assertIn("penalizada", detalhe)

    def test_contexto_recalibracao_reforca_nota_aceite(self) -> None:
        """Feedback repetidamente aceite deve reforcar a confianca da nota."""
        servico = ServicoSugestoes()
        feedbacks = [
            FeedbackSugestaoNota(
                obra_id=1,
                linha_excel=20 + indice,
                descricao="Costa",
                material="MDF",
                artigo="ART_1",
                notas_atual="",
                sugestao_1="Nota Forte",
                score_1=85,
                sugestao_2="",
                score_2=0,
                justificacao="Teste",
                validacao_utilizador="aceite",
                nota_final_utilizador="Nota Forte",
                data_feedback=datetime.now(),
            )
            for indice in range(3)
        ]

        contexto = servico.construir_contexto_recalibracao(feedbacks)
        ajuste, detalhe = servico._calcular_ajuste_recalibracao("Costa", "Nota Forte", contexto)

        self.assertGreater(ajuste, 0)
        self.assertIn("reforcada", detalhe)

    def test_recalibracao_pode_retirar_sugestao_fraca(self) -> None:
        """Uma nota muito penalizada deve deixar de ser sugerida."""
        servico = ServicoSugestoes()

        linha_alvo = LinhaObra(
            obra_id=None,
            estado_origem="TRANSFORMADO_AUTOMATION",
            nome_folha_origem="LISTAGEM_CUT_RITE",
            linha_excel=50,
            descricao="Costa",
            material="MDF Branco",
            artigo="ART_10",
            veio="N",
            esp=19,
            esp_mat=19,
            esp_final=19,
            orla_esq="ABS_1",
            orla_dir="ABS_1",
            notas="",
        )
        historico = [
            LinhaObra(
                obra_id=1,
                estado_origem="TRANSFORMADO_AUTOMATION",
                nome_folha_origem="LISTAGEM_CUT_RITE",
                linha_excel=20,
                descricao="Costa",
                material="MDF Branco",
                artigo="ART_10",
                veio="N",
                esp=19,
                esp_mat=19,
                esp_final=19,
                orla_esq="ABS_1",
                orla_dir="ABS_1",
                notas="Nota Penalizada",
            )
        ]
        feedbacks = [
            FeedbackSugestaoNota(
                obra_id=2,
                linha_excel=60 + indice,
                descricao="Costa",
                material="MDF Branco",
                artigo="ART_10",
                notas_atual="",
                sugestao_1="Nota Penalizada",
                score_1=82,
                sugestao_2="",
                score_2=0,
                justificacao="Teste",
                validacao_utilizador="rejeitada",
                nota_final_utilizador="",
                data_feedback=datetime.now(),
            )
            for indice in range(4)
        ]

        contexto = servico.construir_contexto_recalibracao(feedbacks)
        sugestao = servico.gerar_sugestoes_para_linhas(
            obra_id=10,
            linhas_alvo=[linha_alvo],
            historico=historico,
            usar_recalibracao=True,
            contexto_recalibracao=contexto,
        )[0]

        self.assertEqual(sugestao.sugestao_1, "")

    def test_constroi_relatorio_de_qualidade(self) -> None:
        """Deve agregar contagens e top listas a partir do feedback."""
        servico = ServicoSugestoes()
        feedbacks = [
            FeedbackSugestaoNota(
                obra_id=1,
                linha_excel=10,
                descricao="Costa",
                material="MDF",
                artigo="ART_1",
                notas_atual="",
                sugestao_1="Nota A",
                score_1=90,
                sugestao_2="",
                score_2=0,
                justificacao="Teste",
                validacao_utilizador="aceite",
                nota_final_utilizador="Nota A",
                data_feedback=datetime.now(),
            ),
            FeedbackSugestaoNota(
                obra_id=1,
                linha_excel=11,
                descricao="Costa",
                material="MDF",
                artigo="ART_2",
                notas_atual="",
                sugestao_1="Nota B",
                score_1=70,
                sugestao_2="",
                score_2=0,
                justificacao="Teste",
                validacao_utilizador="rejeitada",
                nota_final_utilizador="",
                data_feedback=datetime.now(),
            ),
            FeedbackSugestaoNota(
                obra_id=1,
                linha_excel=12,
                descricao="Frente",
                material="MDF",
                artigo="ART_3",
                notas_atual="",
                sugestao_1="",
                score_1=0,
                sugestao_2="",
                score_2=0,
                justificacao="Sem sugestao",
                validacao_utilizador="",
                nota_final_utilizador="",
                data_feedback=datetime.now(),
            ),
        ]

        relatorio = servico.construir_relatorio_qualidade(feedbacks)

        self.assertEqual(relatorio.total_linhas_analisadas, 2)
        self.assertEqual(relatorio.total_linhas_com_sugestao, 2)
        self.assertEqual(relatorio.total_linhas_sem_sugestao, 0)
        self.assertEqual(relatorio.total_sugestoes_aceites, 1)
        self.assertEqual(relatorio.total_sugestoes_rejeitadas, 1)
        self.assertEqual(relatorio.total_sugestoes_editadas, 0)
        self.assertEqual(relatorio.top_descricoes_com_mais_acertos[0][0], "Costa")
        self.assertEqual(relatorio.top_notas_mais_rejeitadas[0][0], "Nota B")
        self.assertGreaterEqual(relatorio.cobertura_recalibrada_estimada, 0.0)

    def test_feedback_sem_resposta_manual_e_ignorado(self) -> None:
        """Linhas sem validacao nem nota final nao devem entrar no relatorio."""
        servico = ServicoSugestoes()
        feedback = FeedbackSugestaoNota(
            obra_id=1,
            linha_excel=99,
            descricao="Costa",
            material="MDF",
            artigo="ART_1",
            notas_atual="",
            sugestao_1="Nota A",
            score_1=80,
            sugestao_2="",
            score_2=0,
            justificacao="Teste",
            validacao_utilizador="",
            nota_final_utilizador="",
            data_feedback=datetime.now(),
        )

        self.assertFalse(servico._feedback_tem_resposta_manual(feedback))


if __name__ == "__main__":
    unittest.main()
