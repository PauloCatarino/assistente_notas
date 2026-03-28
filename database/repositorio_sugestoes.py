"""Persistencia simples para sugestoes e feedback manual."""

from __future__ import annotations

from typing import Any

from config.excel_mapeamentos import ESTADO_ORIGEM_TRANSFORMADO
from models.schemas import FeedbackSugestaoNota, LinhaObra


class RepositorioSugestoes:
    """Le historico de notas e guarda feedback de validacao."""

    SQL_CRIAR_TABELA_FEEDBACK = """
        CREATE TABLE IF NOT EXISTS feedback_sugestoes_notas (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            obra_id BIGINT NOT NULL,
            linha_excel INT NOT NULL,
            descricao VARCHAR(255) NULL,
            material VARCHAR(255) NULL,
            artigo VARCHAR(255) NULL,
            notas_atual VARCHAR(500) NULL,
            sugestao_1 VARCHAR(500) NULL,
            score_1 INT NULL,
            sugestao_2 VARCHAR(500) NULL,
            score_2 INT NULL,
            justificacao TEXT NULL,
            validacao_utilizador VARCHAR(100) NULL,
            nota_final_utilizador VARCHAR(500) NULL,
            data_feedback DATETIME NOT NULL,
            criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_feedback_sugestoes_obra
                FOREIGN KEY (obra_id) REFERENCES obras (id),
            CONSTRAINT uk_feedback_sugestao_obra_linha
                UNIQUE (obra_id, linha_excel)
        )
    """

    SQL_CONTAR_OBRAS = """
        SELECT COUNT(*) AS total
        FROM obras
    """

    SQL_CONTAR_LINHAS_COM_NOTA = """
        SELECT COUNT(*) AS total
        FROM linhas_obra
        WHERE estado_origem = %s
          AND COALESCE(TRIM(notas), '') <> ''
    """

    SQL_LISTAR_HISTORICO_NOTAS = """
        SELECT
            id,
            obra_id,
            estado_origem,
            nome_folha_origem,
            linha_excel,
            numero_linha,
            chave_ligacao,
            referencia,
            designacao,
            descricao,
            material,
            comp,
            larg,
            esp,
            qt,
            veio,
            orla_esq,
            orla_dir,
            orla_cima,
            orla_baixo,
            cnc_1_raw,
            cnc_2_raw,
            enc,
            cliente,
            ref_cliente,
            processo,
            artigo,
            notas,
            id_linha_excel,
            esp_mat,
            esp_final
        FROM linhas_obra
        WHERE estado_origem = %s
          AND COALESCE(TRIM(notas), '') <> ''
          AND (%s IS NULL OR obra_id <> %s)
        ORDER BY obra_id, id
    """

    SQL_INSERIR_OU_ATUALIZAR_FEEDBACK = """
        INSERT INTO feedback_sugestoes_notas (
            obra_id,
            linha_excel,
            descricao,
            material,
            artigo,
            notas_atual,
            sugestao_1,
            score_1,
            sugestao_2,
            score_2,
            justificacao,
            validacao_utilizador,
            nota_final_utilizador,
            data_feedback
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            descricao = VALUES(descricao),
            material = VALUES(material),
            artigo = VALUES(artigo),
            notas_atual = VALUES(notas_atual),
            sugestao_1 = VALUES(sugestao_1),
            score_1 = VALUES(score_1),
            sugestao_2 = VALUES(sugestao_2),
            score_2 = VALUES(score_2),
            justificacao = VALUES(justificacao),
            validacao_utilizador = VALUES(validacao_utilizador),
            nota_final_utilizador = VALUES(nota_final_utilizador),
            data_feedback = VALUES(data_feedback)
    """

    SQL_LISTAR_FEEDBACK_TODOS = """
        SELECT
            obra_id,
            linha_excel,
            descricao,
            material,
            artigo,
            notas_atual,
            sugestao_1,
            score_1,
            sugestao_2,
            score_2,
            justificacao,
            validacao_utilizador,
            nota_final_utilizador,
            data_feedback
        FROM feedback_sugestoes_notas
        ORDER BY obra_id, linha_excel
    """

    SQL_LISTAR_FEEDBACK_POR_OBRA = """
        SELECT
            obra_id,
            linha_excel,
            descricao,
            material,
            artigo,
            notas_atual,
            sugestao_1,
            score_1,
            sugestao_2,
            score_2,
            justificacao,
            validacao_utilizador,
            nota_final_utilizador,
            data_feedback
        FROM feedback_sugestoes_notas
        WHERE obra_id = %s
        ORDER BY obra_id, linha_excel
    """

    def preparar_estrutura_feedback(self, conexao: Any) -> None:
        """Garante a tabela de feedback manual."""
        cursor = conexao.cursor()

        try:
            cursor.execute(self.SQL_CRIAR_TABELA_FEEDBACK)
        finally:
            cursor.close()

    def contar_obras(self, conexao: Any) -> int:
        """Conta o numero total de obras registadas."""
        cursor = conexao.cursor(dictionary=True)

        try:
            cursor.execute(self.SQL_CONTAR_OBRAS)
            linha = cursor.fetchone() or {}
            return int(linha.get("total", 0))
        finally:
            cursor.close()

    def contar_linhas_com_nota_historica(self, conexao: Any, excluir_obra_id: int | None = None) -> int:
        """Conta linhas com nota historica util para sugestoes."""
        cursor = conexao.cursor(dictionary=True)

        try:
            if excluir_obra_id is None:
                cursor.execute(self.SQL_CONTAR_LINHAS_COM_NOTA, (ESTADO_ORIGEM_TRANSFORMADO,))
                linha = cursor.fetchone() or {}
                return int(linha.get("total", 0))

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM linhas_obra
                WHERE estado_origem = %s
                  AND COALESCE(TRIM(notas), '') <> ''
                  AND obra_id <> %s
                """,
                (ESTADO_ORIGEM_TRANSFORMADO, excluir_obra_id),
            )
            linha = cursor.fetchone() or {}
            return int(linha.get("total", 0))
        finally:
            cursor.close()

    def listar_linhas_historicas_com_nota(
        self,
        conexao: Any,
        excluir_obra_id: int | None = None,
    ) -> list[LinhaObra]:
        """Le as linhas historicas com nota preenchida."""
        cursor = conexao.cursor(dictionary=True)

        try:
            cursor.execute(
                self.SQL_LISTAR_HISTORICO_NOTAS,
                (ESTADO_ORIGEM_TRANSFORMADO, excluir_obra_id, excluir_obra_id),
            )
            registos = cursor.fetchall()
        finally:
            cursor.close()

        linhas: list[LinhaObra] = []

        for registo in registos:
            linhas.append(
                LinhaObra(
                    id=int(registo["id"]),
                    obra_id=int(registo["obra_id"]),
                    estado_origem=str(registo["estado_origem"]),
                    nome_folha_origem=str(registo["nome_folha_origem"]),
                    linha_excel=int(registo["linha_excel"]),
                    numero_linha=int(registo["numero_linha"]),
                    chave_ligacao=str(registo["chave_ligacao"] or ""),
                    referencia=str(registo["referencia"] or ""),
                    designacao=str(registo["designacao"] or ""),
                    descricao=str(registo["descricao"] or ""),
                    material=str(registo["material"] or ""),
                    comp=float(registo["comp"]) if registo["comp"] is not None else None,
                    larg=float(registo["larg"]) if registo["larg"] is not None else None,
                    esp=float(registo["esp"]) if registo["esp"] is not None else None,
                    qt=float(registo["qt"]) if registo["qt"] is not None else None,
                    veio=str(registo["veio"] or ""),
                    orla_esq=str(registo["orla_esq"] or ""),
                    orla_dir=str(registo["orla_dir"] or ""),
                    orla_cima=str(registo["orla_cima"] or ""),
                    orla_baixo=str(registo["orla_baixo"] or ""),
                    cnc_1_raw=str(registo["cnc_1_raw"] or ""),
                    cnc_2_raw=str(registo["cnc_2_raw"] or ""),
                    enc=str(registo["enc"] or ""),
                    cliente=str(registo["cliente"] or ""),
                    ref_cliente=str(registo["ref_cliente"] or ""),
                    processo=str(registo["processo"] or ""),
                    artigo=str(registo["artigo"] or ""),
                    notas=str(registo["notas"] or ""),
                    id_linha_excel=str(registo["id_linha_excel"] or ""),
                    esp_mat=float(registo["esp_mat"]) if registo["esp_mat"] is not None else None,
                    esp_final=float(registo["esp_final"]) if registo["esp_final"] is not None else None,
                )
            )

        return linhas

    def guardar_feedback(self, conexao: Any, feedbacks: list[FeedbackSugestaoNota]) -> int:
        """Guarda ou atualiza o feedback manual importado do Excel."""
        if not feedbacks:
            return 0

        cursor = conexao.cursor()

        try:
            parametros = [
                (
                    feedback.obra_id,
                    feedback.linha_excel,
                    feedback.descricao or None,
                    feedback.material or None,
                    feedback.artigo or None,
                    feedback.notas_atual or None,
                    feedback.sugestao_1 or None,
                    feedback.score_1,
                    feedback.sugestao_2 or None,
                    feedback.score_2,
                    feedback.justificacao or None,
                    feedback.validacao_utilizador or None,
                    feedback.nota_final_utilizador or None,
                    feedback.data_feedback,
                )
                for feedback in feedbacks
            ]
            cursor.executemany(self.SQL_INSERIR_OU_ATUALIZAR_FEEDBACK, parametros)
            if cursor.rowcount and cursor.rowcount > 0:
                return int(cursor.rowcount)
            return len(feedbacks)
        finally:
            cursor.close()

    def listar_feedback(self, conexao: Any, obra_id: int | None = None) -> list[FeedbackSugestaoNota]:
        """Le o feedback guardado para avaliacao de qualidade."""
        cursor = conexao.cursor(dictionary=True)

        try:
            if obra_id is None:
                cursor.execute(self.SQL_LISTAR_FEEDBACK_TODOS)
            else:
                cursor.execute(self.SQL_LISTAR_FEEDBACK_POR_OBRA, (obra_id,))
            registos = cursor.fetchall()
        finally:
            cursor.close()

        feedbacks: list[FeedbackSugestaoNota] = []

        for registo in registos:
            feedbacks.append(
                FeedbackSugestaoNota(
                    obra_id=int(registo["obra_id"]),
                    linha_excel=int(registo["linha_excel"]),
                    descricao=str(registo["descricao"] or ""),
                    material=str(registo["material"] or ""),
                    artigo=str(registo["artigo"] or ""),
                    notas_atual=str(registo["notas_atual"] or ""),
                    sugestao_1=str(registo["sugestao_1"] or ""),
                    score_1=int(registo["score_1"] or 0),
                    sugestao_2=str(registo["sugestao_2"] or ""),
                    score_2=int(registo["score_2"] or 0),
                    justificacao=str(registo["justificacao"] or ""),
                    validacao_utilizador=str(registo["validacao_utilizador"] or ""),
                    nota_final_utilizador=str(registo["nota_final_utilizador"] or ""),
                    data_feedback=registo["data_feedback"],
                )
            )

        return feedbacks
