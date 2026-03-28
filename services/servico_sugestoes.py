"""Servico simples para sugestoes, validacao manual e feedback."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import ConfiguracaoProjeto, carregar_configuracoes
from config.sugestoes_notas import (
    COLUNAS_EXPORTACAO_VALIDACAO,
    VALIDACOES_ACEITES,
    VALIDACOES_EDITADAS,
    VALIDACOES_REJEITADAS,
)
from database.db_connection import GestorLigacaoMySQL
from database.repositorio_importacao_excel import RepositorioImportacaoExcel
from database.repositorio_sugestoes import RepositorioSugestoes
from importers.importar_excel_cutrite import ImportadorFolhasExcel
from importers.importar_obras import ImportadorObras
from models.schemas import (
    FeedbackSugestaoNota,
    LinhaObra,
    RelatorioQualidadeSugestoes,
    ResultadoAnaliseSugestoesExcel,
    ResultadoImportacaoFeedbackSugestoes,
    SugestaoNotaLinhaExcel,
)
from utils.chave_ligacao import normalizar_numero_para_comparacao, normalizar_texto_para_comparacao
from utils.helpers import converter_para_numero, limpar_texto, normalizar_texto_chave

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font
except ImportError:  # pragma: no cover - fallback simples
    Workbook = None
    Font = None
    load_workbook = None


class ServicoSugestoes:
    """Centraliza o primeiro ciclo pratico de validacao do assistente.

    Esta fase cobre:
    - sugestoes simples com historico MySQL
    - exportacao para CSV e/ou Excel
    - importacao do feedback preenchido manualmente
    - relatorio de qualidade baseado nesse feedback
    """

    PESOS_CAMPOS = {
        "descricao": 25,
        "material": 20,
        "artigo": 15,
        "veio": 5,
        "esp": 10,
        "esp_mat": 5,
        "esp_final": 5,
        "orla_esq": 5,
        "orla_dir": 5,
        "orla_cima": 3,
        "orla_baixo": 2,
    }
    LIMIAR_CANDIDATO = 45
    LIMIAR_SUGESTAO = 65

    def __init__(self, configuracao: ConfiguracaoProjeto | None = None) -> None:
        """Prepara dependencias do motor de sugestoes."""
        self.configuracao = configuracao or carregar_configuracoes()
        self.importador_obras = ImportadorObras(self.configuracao.base_dir)
        self.importador_folhas = ImportadorFolhasExcel()
        self.gestor_bd = GestorLigacaoMySQL(self.configuracao)
        self.repositorio_importacao = RepositorioImportacaoExcel()
        self.repositorio_sugestoes = RepositorioSugestoes()

    def analisar_ficheiro_excel(
        self,
        caminho_ficheiro: Path,
        caminho_csv_saida: Path | None = None,
        caminho_excel_saida: Path | None = None,
        gerar_csv: bool = False,
        gerar_excel: bool = True,
    ) -> ResultadoAnaliseSugestoesExcel:
        """Analisa um ficheiro Excel e gera ficheiros de validacao.

        Por omissao gera um `.xlsx`, porque e mais comodo para validacao
        manual no Excel sem tocar no ficheiro original.
        """
        caminho_ficheiro = Path(caminho_ficheiro).resolve()
        if not caminho_ficheiro.exists():
            raise FileNotFoundError(f"Ficheiro nao encontrado: {caminho_ficheiro}")

        if not gerar_csv and not gerar_excel:
            gerar_excel = True

        obra_excel = self.importador_obras.ler_metadados_obra(caminho_ficheiro)
        resultados_folhas = self.importador_folhas.ler_folhas_configuradas(caminho_ficheiro)
        resultado_folha = self._selecionar_folha_para_sugestoes(resultados_folhas)

        conexao = self.gestor_bd.criar_conexao()
        if conexao is None:
            raise RuntimeError(
                "Nao foi possivel criar ligacao ao MySQL. Verifique o ficheiro .env e a disponibilidade do servidor."
            )

        try:
            self.repositorio_importacao.preparar_estrutura_importacao(conexao)
            self.repositorio_sugestoes.preparar_estrutura_feedback(conexao)
            obra_existente = self.repositorio_importacao.procurar_obra_existente(conexao, obra_excel)
            obra_id_excluir = int(obra_existente["id"]) if obra_existente else None

            total_obras_historico = self.repositorio_sugestoes.contar_obras(conexao)
            total_linhas_com_nota_historica = self.repositorio_sugestoes.contar_linhas_com_nota_historica(
                conexao,
                excluir_obra_id=obra_id_excluir,
            )
            historico = self.repositorio_sugestoes.listar_linhas_historicas_com_nota(
                conexao,
                excluir_obra_id=obra_id_excluir,
            )
        finally:
            self.gestor_bd.fechar_conexao(conexao)

        if obra_id_excluir is not None and total_obras_historico > 0:
            total_obras_historico -= 1

        sugestoes = self.gerar_sugestoes_para_linhas(
            obra_id=obra_id_excluir,
            linhas_alvo=resultado_folha.linhas,
            historico=historico,
        )

        if caminho_csv_saida is None and gerar_csv:
            caminho_csv_saida = self.configuracao.logs_dir / f"validacao_sugestoes_{caminho_ficheiro.stem}.csv"
        if caminho_excel_saida is None and gerar_excel:
            caminho_excel_saida = self.configuracao.logs_dir / f"validacao_sugestoes_{caminho_ficheiro.stem}.xlsx"

        caminho_csv_final = ""
        caminho_excel_final = ""

        if gerar_csv and caminho_csv_saida is not None:
            caminho_csv_saida = Path(caminho_csv_saida).resolve()
            self.exportar_csv_validacao(caminho_csv_saida, sugestoes)
            caminho_csv_final = str(caminho_csv_saida)

        if gerar_excel and caminho_excel_saida is not None:
            caminho_excel_saida = Path(caminho_excel_saida).resolve()
            self.exportar_excel_validacao(caminho_excel_saida, sugestoes)
            caminho_excel_final = str(caminho_excel_saida)

        total_sugestoes_geradas = sum(1 for sugestao in sugestoes if sugestao.sugestao_1)
        total_linhas_sem_sugestao = len(sugestoes) - total_sugestoes_geradas

        return ResultadoAnaliseSugestoesExcel(
            caminho_ficheiro=str(caminho_ficheiro),
            nome_folha_analisada=resultado_folha.nome_folha_real,
            obra_id=obra_id_excluir,
            total_obras_historico=total_obras_historico,
            total_linhas_com_nota_historica=total_linhas_com_nota_historica,
            total_linhas_analisadas=len(sugestoes),
            total_sugestoes_geradas=total_sugestoes_geradas,
            total_linhas_sem_sugestao=total_linhas_sem_sugestao,
            caminho_csv_saida=caminho_csv_final,
            caminho_excel_saida=caminho_excel_final,
            sugestoes=sugestoes,
        )

    def importar_feedback_validacao(self, caminho_ficheiro: Path) -> ResultadoImportacaoFeedbackSugestoes:
        """Importa feedback preenchido num CSV ou Excel de validacao."""
        caminho_ficheiro = Path(caminho_ficheiro).resolve()
        if not caminho_ficheiro.exists():
            raise FileNotFoundError(f"Ficheiro nao encontrado: {caminho_ficheiro}")

        feedbacks_lidos = self._ler_feedback_de_ficheiro(caminho_ficheiro)
        feedbacks_validos = [feedback for feedback in feedbacks_lidos if feedback.obra_id and feedback.linha_excel]
        total_ignorados = len(feedbacks_lidos) - len(feedbacks_validos)

        conexao = self.gestor_bd.criar_conexao()
        if conexao is None:
            raise RuntimeError(
                "Nao foi possivel criar ligacao ao MySQL. Verifique o ficheiro .env e a disponibilidade do servidor."
            )

        try:
            self.repositorio_importacao.preparar_estrutura_importacao(conexao)
            self.repositorio_sugestoes.preparar_estrutura_feedback(conexao)
            total_importado = self.repositorio_sugestoes.guardar_feedback(conexao, feedbacks_validos)
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
        finally:
            self.gestor_bd.fechar_conexao(conexao)

        return ResultadoImportacaoFeedbackSugestoes(
            caminho_ficheiro=str(caminho_ficheiro),
            total_registos_lidos=len(feedbacks_lidos),
            total_registos_importados=total_importado,
            total_registos_ignorados=total_ignorados,
        )

    def gerar_relatorio_qualidade(self, obra_id: int | None = None) -> RelatorioQualidadeSugestoes:
        """Gera um relatorio simples com base no feedback guardado."""
        conexao = self.gestor_bd.criar_conexao()
        if conexao is None:
            raise RuntimeError(
                "Nao foi possivel criar ligacao ao MySQL. Verifique o ficheiro .env e a disponibilidade do servidor."
            )

        try:
            self.repositorio_sugestoes.preparar_estrutura_feedback(conexao)
            feedbacks = self.repositorio_sugestoes.listar_feedback(conexao, obra_id=obra_id)
        finally:
            self.gestor_bd.fechar_conexao(conexao)

        return self.construir_relatorio_qualidade(feedbacks)

    def gerar_sugestoes_para_linhas(
        self,
        obra_id: int | None,
        linhas_alvo: list[LinhaObra],
        historico: list[LinhaObra],
    ) -> list[SugestaoNotaLinhaExcel]:
        """Gera sugestoes simples para cada linha lida do Excel."""
        sugestoes: list[SugestaoNotaLinhaExcel] = []

        for linha_alvo in linhas_alvo:
            sugestoes.append(self._gerar_sugestao_para_linha(obra_id, linha_alvo, historico))

        return sugestoes

    def construir_relatorio_qualidade(
        self,
        feedbacks: list[FeedbackSugestaoNota],
    ) -> RelatorioQualidadeSugestoes:
        """Constroi o relatorio de qualidade a partir do feedback carregado."""
        total_linhas_analisadas = len(feedbacks)
        total_linhas_com_sugestao = sum(1 for feedback in feedbacks if feedback.sugestao_1.strip())
        total_linhas_sem_sugestao = total_linhas_analisadas - total_linhas_com_sugestao

        estados_feedback = [
            (feedback, self.normalizar_estado_feedback(feedback.validacao_utilizador, feedback.sugestao_1, feedback.nota_final_utilizador))
            for feedback in feedbacks
        ]

        total_sugestoes_aceites = sum(1 for _, estado in estados_feedback if estado == "ACEITE")
        total_sugestoes_rejeitadas = sum(1 for _, estado in estados_feedback if estado == "REJEITADA")
        total_sugestoes_editadas = sum(1 for _, estado in estados_feedback if estado == "EDITADA")

        taxa_cobertura = self._calcular_percentagem(total_linhas_com_sugestao, total_linhas_analisadas)
        taxa_aceitacao = self._calcular_percentagem(total_sugestoes_aceites, total_linhas_com_sugestao)
        taxa_rejeicao = self._calcular_percentagem(total_sugestoes_rejeitadas, total_linhas_com_sugestao)

        descricoes_acertos = Counter(
            feedback.descricao for feedback, estado in estados_feedback if estado == "ACEITE" and feedback.descricao
        )
        descricoes_falhas = Counter(
            feedback.descricao
            for feedback, estado in estados_feedback
            if estado in {"REJEITADA", "EDITADA"} and feedback.descricao
        )
        notas_aceites = Counter(
            feedback.sugestao_1 for feedback, estado in estados_feedback if estado == "ACEITE" and feedback.sugestao_1
        )
        notas_rejeitadas = Counter(
            feedback.sugestao_1 for feedback, estado in estados_feedback if estado == "REJEITADA" and feedback.sugestao_1
        )

        return RelatorioQualidadeSugestoes(
            total_linhas_analisadas=total_linhas_analisadas,
            total_linhas_com_sugestao=total_linhas_com_sugestao,
            total_linhas_sem_sugestao=total_linhas_sem_sugestao,
            total_sugestoes_aceites=total_sugestoes_aceites,
            total_sugestoes_rejeitadas=total_sugestoes_rejeitadas,
            total_sugestoes_editadas=total_sugestoes_editadas,
            taxa_cobertura=taxa_cobertura,
            taxa_aceitacao=taxa_aceitacao,
            taxa_rejeicao=taxa_rejeicao,
            top_descricoes_com_mais_acertos=descricoes_acertos.most_common(5),
            top_descricoes_com_mais_falhas=descricoes_falhas.most_common(5),
            top_notas_mais_aceites=notas_aceites.most_common(5),
            top_notas_mais_rejeitadas=notas_rejeitadas.most_common(5),
        )

    def calcular_score_sugestao(self, linha_alvo: LinhaObra, linha_historica: LinhaObra) -> tuple[int, list[str]]:
        """Calcula um score simples entre uma linha alvo e uma linha historica."""
        score = 0
        campos_coincidentes: list[str] = []

        for campo_texto in ("descricao", "material", "artigo", "veio", "orla_esq", "orla_dir", "orla_cima", "orla_baixo"):
            score, campos_coincidentes = self._somar_score_texto(
                linha_alvo,
                linha_historica,
                campo_texto,
                score,
                campos_coincidentes,
            )

        for campo_numero in ("esp", "esp_mat", "esp_final"):
            score, campos_coincidentes = self._somar_score_numero(
                linha_alvo,
                linha_historica,
                campo_numero,
                score,
                campos_coincidentes,
            )

        campos_principais = {"descricao", "material", "artigo"}
        if not campos_principais.intersection(campos_coincidentes):
            return 0, []

        return min(score, 100), campos_coincidentes

    def exportar_csv_validacao(
        self,
        caminho_csv_saida: Path,
        sugestoes: list[SugestaoNotaLinhaExcel],
    ) -> None:
        """Exporta um CSV com colunas prontas para validacao manual."""
        caminho_csv_saida = Path(caminho_csv_saida)
        caminho_csv_saida.parent.mkdir(parents=True, exist_ok=True)

        with caminho_csv_saida.open("w", encoding="utf-8-sig", newline="") as ficheiro_csv:
            escritor = csv.writer(ficheiro_csv, delimiter=";")
            escritor.writerow(COLUNAS_EXPORTACAO_VALIDACAO)

            for sugestao in sugestoes:
                escritor.writerow(self._linha_para_exportacao(sugestao))

    def exportar_excel_validacao(
        self,
        caminho_excel_saida: Path,
        sugestoes: list[SugestaoNotaLinhaExcel],
    ) -> None:
        """Exporta um ficheiro Excel simples para validacao manual."""
        if Workbook is None or Font is None:
            raise RuntimeError("Instale `openpyxl` para gerar o ficheiro Excel de validacao.")

        caminho_excel_saida = Path(caminho_excel_saida)
        caminho_excel_saida.parent.mkdir(parents=True, exist_ok=True)

        workbook = Workbook()
        folha = workbook.active
        folha.title = "validacao_sugestoes"
        folha.append(list(COLUNAS_EXPORTACAO_VALIDACAO))

        for celula in folha[1]:
            celula.font = Font(bold=True)

        for sugestao in sugestoes:
            folha.append(self._linha_para_exportacao(sugestao))

        folha.freeze_panes = "A2"
        folha.auto_filter.ref = folha.dimensions

        larguras = {
            "A": 10,
            "B": 12,
            "C": 30,
            "D": 40,
            "E": 20,
            "F": 20,
            "G": 40,
            "H": 10,
            "I": 40,
            "J": 10,
            "K": 60,
            "L": 18,
            "M": 30,
        }
        for coluna, largura in larguras.items():
            folha.column_dimensions[coluna].width = largura

        workbook.save(caminho_excel_saida)
        workbook.close()

    def normalizar_estado_feedback(
        self,
        validacao_utilizador: str,
        sugestao_1: str,
        nota_final_utilizador: str,
    ) -> str:
        """Normaliza o feedback manual para estados simples e comparaveis."""
        validacao_normalizada = normalizar_texto_para_comparacao(validacao_utilizador)
        sugestao_normalizada = normalizar_texto_para_comparacao(sugestao_1)
        nota_final_normalizada = normalizar_texto_para_comparacao(nota_final_utilizador)

        if validacao_normalizada in VALIDACOES_ACEITES:
            return "ACEITE"
        if validacao_normalizada in VALIDACOES_REJEITADAS:
            return "REJEITADA"
        if validacao_normalizada in VALIDACOES_EDITADAS:
            return "EDITADA"

        if sugestao_normalizada and nota_final_normalizada:
            if sugestao_normalizada == nota_final_normalizada:
                return "ACEITE"
            return "EDITADA"

        return "SEM_RESPOSTA"

    def _gerar_sugestao_para_linha(
        self,
        obra_id: int | None,
        linha_alvo: LinhaObra,
        historico: list[LinhaObra],
    ) -> SugestaoNotaLinhaExcel:
        """Gera as duas melhores sugestoes para uma linha."""
        candidatos_por_nota: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "melhor_score": 0,
                "ocorrencias": 0,
                "campos": [],
            }
        )

        for linha_historica in historico:
            score, campos_coincidentes = self.calcular_score_sugestao(linha_alvo, linha_historica)
            if score < self.LIMIAR_CANDIDATO:
                continue

            nota_historica = (linha_historica.notas or "").strip()
            if not nota_historica:
                continue

            agregado = candidatos_por_nota[nota_historica]
            agregado["ocorrencias"] += 1

            if score > agregado["melhor_score"]:
                agregado["melhor_score"] = score
                agregado["campos"] = campos_coincidentes

        sugestoes_ordenadas: list[tuple[str, int, int, list[str]]] = []

        for nota_historica, dados in candidatos_por_nota.items():
            score_final = min(100, dados["melhor_score"] + min(10, (dados["ocorrencias"] - 1) * 5))
            sugestoes_ordenadas.append(
                (
                    nota_historica,
                    score_final,
                    int(dados["ocorrencias"]),
                    list(dados["campos"]),
                )
            )

        sugestoes_ordenadas.sort(key=lambda item: (-item[1], -item[2], item[0]))
        sugestoes_finais = [item for item in sugestoes_ordenadas if item[1] >= self.LIMIAR_SUGESTAO][:2]

        if not sugestoes_finais:
            justificacao = "Sem historico suficiente para sugerir nota com seguranca."
            if sugestoes_ordenadas:
                justificacao = "Existe historico, mas abaixo do limiar minimo de confianca."

            return SugestaoNotaLinhaExcel(
                obra_id=obra_id,
                linha_excel=linha_alvo.linha_excel,
                descricao=linha_alvo.descricao,
                material=linha_alvo.material,
                artigo=linha_alvo.artigo,
                notas_atual=linha_alvo.notas,
                justificacao=justificacao,
            )

        nota_1, score_1, ocorrencias_1, campos_1 = sugestoes_finais[0]
        nota_2 = ""
        score_2 = 0

        if len(sugestoes_finais) > 1:
            nota_2, score_2, _, _ = sugestoes_finais[1]

        lista_campos = ", ".join(campos_1[:6]) if campos_1 else "sem campos fortes"
        justificacao = (
            f"{ocorrencias_1} linha(s) historica(s) semelhante(s); "
            f"campos coincidentes: {lista_campos}."
        )

        return SugestaoNotaLinhaExcel(
            obra_id=obra_id,
            linha_excel=linha_alvo.linha_excel,
            descricao=linha_alvo.descricao,
            material=linha_alvo.material,
            artigo=linha_alvo.artigo,
            notas_atual=linha_alvo.notas,
            sugestao_1=nota_1,
            score_1=score_1,
            sugestao_2=nota_2,
            score_2=score_2,
            justificacao=justificacao,
        )

    def _ler_feedback_de_ficheiro(self, caminho_ficheiro: Path) -> list[FeedbackSugestaoNota]:
        """Le feedback a partir de CSV ou Excel gerado para validacao."""
        extensao = caminho_ficheiro.suffix.lower()

        if extensao == ".csv":
            return self._ler_feedback_csv(caminho_ficheiro)

        if extensao in {".xlsx", ".xlsm"}:
            return self._ler_feedback_excel(caminho_ficheiro)

        raise ValueError("Formato de feedback nao suportado. Use .csv, .xlsx ou .xlsm.")

    def _ler_feedback_csv(self, caminho_ficheiro: Path) -> list[FeedbackSugestaoNota]:
        """Le feedback manual a partir de CSV."""
        feedbacks: list[FeedbackSugestaoNota] = []

        with Path(caminho_ficheiro).open("r", encoding="utf-8-sig", newline="") as ficheiro_csv:
            leitor = csv.DictReader(ficheiro_csv, delimiter=";")
            for linha in leitor:
                feedback = self._criar_feedback_a_partir_de_linha(linha)
                if feedback is not None:
                    feedbacks.append(feedback)

        return feedbacks

    def _ler_feedback_excel(self, caminho_ficheiro: Path) -> list[FeedbackSugestaoNota]:
        """Le feedback manual a partir de um Excel de validacao."""
        if load_workbook is None:
            raise RuntimeError("Instale `openpyxl` para ler o ficheiro Excel de feedback.")

        workbook = load_workbook(filename=caminho_ficheiro, read_only=True, data_only=True)
        feedbacks: list[FeedbackSugestaoNota] = []

        try:
            folha = workbook.active
            linhas = folha.iter_rows(values_only=True)
            cabecalhos = next(linhas, None)
            if cabecalhos is None:
                return []

            chaves = [normalizar_texto_chave(cabecalho) for cabecalho in cabecalhos]

            for valores in linhas:
                dados_linha = {
                    chaves[indice]: valores[indice]
                    for indice in range(min(len(chaves), len(valores)))
                    if chaves[indice]
                }
                feedback = self._criar_feedback_a_partir_de_linha(dados_linha)
                if feedback is not None:
                    feedbacks.append(feedback)
        finally:
            workbook.close()

        return feedbacks

    def _criar_feedback_a_partir_de_linha(self, dados_linha: dict[str, Any]) -> FeedbackSugestaoNota | None:
        """Converte uma linha lida do ficheiro de validacao em feedback estruturado."""
        obra_id = int(converter_para_numero(dados_linha.get("obra_id")) or 0)
        linha_excel = int(converter_para_numero(dados_linha.get("linha_excel")) or 0)

        if obra_id <= 0 or linha_excel <= 0:
            return None

        return FeedbackSugestaoNota(
            obra_id=obra_id,
            linha_excel=linha_excel,
            descricao=limpar_texto(dados_linha.get("descricao")),
            material=limpar_texto(dados_linha.get("material")),
            artigo=limpar_texto(dados_linha.get("artigo")),
            notas_atual=limpar_texto(dados_linha.get("notas_atual")),
            sugestao_1=limpar_texto(dados_linha.get("sugestao_1")),
            score_1=int(converter_para_numero(dados_linha.get("score_1")) or 0),
            sugestao_2=limpar_texto(dados_linha.get("sugestao_2")),
            score_2=int(converter_para_numero(dados_linha.get("score_2")) or 0),
            justificacao=limpar_texto(dados_linha.get("justificacao")),
            validacao_utilizador=limpar_texto(dados_linha.get("validacao_utilizador")),
            nota_final_utilizador=limpar_texto(dados_linha.get("nota_final_utilizador")),
            data_feedback=datetime.now(),
        )

    def _linha_para_exportacao(self, sugestao: SugestaoNotaLinhaExcel) -> list[Any]:
        """Converte a sugestao numa linha pronta para CSV ou Excel."""
        return [
            sugestao.obra_id or "",
            sugestao.linha_excel,
            sugestao.descricao,
            sugestao.material,
            sugestao.artigo,
            sugestao.notas_atual,
            sugestao.sugestao_1,
            sugestao.score_1,
            sugestao.sugestao_2,
            sugestao.score_2,
            sugestao.justificacao,
            sugestao.validacao_utilizador,
            sugestao.nota_final_utilizador,
        ]

    def _selecionar_folha_para_sugestoes(self, resultados_folhas: list[Any]) -> Any:
        """Escolhe a melhor folha para gerar sugestoes."""
        for resultado in resultados_folhas:
            if resultado.nome_folha_esperada == "LISTAGEM_CUT_RITE":
                return resultado

        for resultado in resultados_folhas:
            if resultado.linhas:
                return resultado

        raise ValueError("Nao foi encontrada nenhuma folha com linhas para analisar.")

    def _somar_score_texto(
        self,
        linha_alvo: LinhaObra,
        linha_historica: LinhaObra,
        campo: str,
        score_atual: int,
        campos_coincidentes: list[str],
    ) -> tuple[int, list[str]]:
        """Soma score quando um campo textual coincide apos normalizacao."""
        valor_alvo = normalizar_texto_para_comparacao(getattr(linha_alvo, campo, ""))
        valor_historico = normalizar_texto_para_comparacao(getattr(linha_historica, campo, ""))

        if valor_alvo and valor_alvo == valor_historico:
            return score_atual + self.PESOS_CAMPOS[campo], campos_coincidentes + [campo]

        return score_atual, campos_coincidentes

    def _somar_score_numero(
        self,
        linha_alvo: LinhaObra,
        linha_historica: LinhaObra,
        campo: str,
        score_atual: int,
        campos_coincidentes: list[str],
    ) -> tuple[int, list[str]]:
        """Soma score quando um campo numerico coincide dentro de tolerancia simples."""
        valor_alvo = normalizar_numero_para_comparacao(getattr(linha_alvo, campo, None))
        valor_historico = normalizar_numero_para_comparacao(getattr(linha_historica, campo, None))

        if valor_alvo is None or valor_historico is None:
            return score_atual, campos_coincidentes

        if abs(valor_alvo - valor_historico) <= 0.2:
            return score_atual + self.PESOS_CAMPOS[campo], campos_coincidentes + [campo]

        return score_atual, campos_coincidentes

    @staticmethod
    def _calcular_percentagem(parte: int, total: int) -> float:
        """Calcula percentagem simples com duas casas."""
        if total <= 0:
            return 0.0

        return round((parte / total) * 100, 2)
