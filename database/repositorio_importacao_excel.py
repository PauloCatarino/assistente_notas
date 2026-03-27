"""Persistência simples para importação Excel -> MySQL."""

from __future__ import annotations

import json
from typing import Any

from models.schemas import LinhaObra, ObraExcel


class RepositorioImportacaoExcel:
    """Concentra as operações de base de dados usadas nesta fase do projeto."""

    SQL_CRIAR_TABELA_OBRAS = """
        CREATE TABLE IF NOT EXISTS obras (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            codigo_obra VARCHAR(100) NULL,
            nome_obra VARCHAR(255) NOT NULL,
            ficheiro_origem VARCHAR(500) NOT NULL,
            folha_origem VARCHAR(100) NOT NULL DEFAULT 'IMPORTACAO_EXCEL',
            observacoes TEXT NULL,
            criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """

    SQL_CRIAR_TABELA_LINHAS_OBRA = """
        CREATE TABLE IF NOT EXISTS linhas_obra (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            obra_id BIGINT NOT NULL,
            numero_linha INT NOT NULL,
            linha_excel INT NOT NULL,
            estado_origem VARCHAR(50) NOT NULL,
            nome_folha_origem VARCHAR(100) NOT NULL,
            referencia VARCHAR(150) NULL,
            designacao VARCHAR(255) NULL,
            descricao VARCHAR(255) NULL,
            material VARCHAR(255) NULL,
            comp DECIMAL(12,3) NULL,
            larg DECIMAL(12,3) NULL,
            esp DECIMAL(12,3) NULL,
            qt DECIMAL(12,3) NULL,
            veio VARCHAR(50) NULL,
            orla_esq VARCHAR(255) NULL,
            orla_dir VARCHAR(255) NULL,
            orla_cima VARCHAR(255) NULL,
            orla_baixo VARCHAR(255) NULL,
            cnc_1_raw VARCHAR(255) NULL,
            cnc_2_raw VARCHAR(255) NULL,
            enc VARCHAR(100) NULL,
            cliente VARCHAR(255) NULL,
            ref_cliente VARCHAR(255) NULL,
            processo VARCHAR(255) NULL,
            artigo VARCHAR(255) NULL,
            notas VARCHAR(500) NULL,
            id_linha_excel VARCHAR(100) NULL,
            esp_mat DECIMAL(12,3) NULL,
            esp_final DECIMAL(12,3) NULL,
            dados_json JSON NULL,
            criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_linhas_obra_obras
                FOREIGN KEY (obra_id) REFERENCES obras (id)
        )
    """

    DEFINICOES_COLUNAS_LINHAS_OBRA = {
        "linha_excel": "INT NULL",
        "estado_origem": "VARCHAR(50) NULL",
        "nome_folha_origem": "VARCHAR(100) NULL",
        "descricao": "VARCHAR(255) NULL",
        "material": "VARCHAR(255) NULL",
        "comp": "DECIMAL(12,3) NULL",
        "larg": "DECIMAL(12,3) NULL",
        "esp": "DECIMAL(12,3) NULL",
        "qt": "DECIMAL(12,3) NULL",
        "veio": "VARCHAR(50) NULL",
        "orla_esq": "VARCHAR(255) NULL",
        "orla_dir": "VARCHAR(255) NULL",
        "orla_cima": "VARCHAR(255) NULL",
        "orla_baixo": "VARCHAR(255) NULL",
        "cnc_1_raw": "VARCHAR(255) NULL",
        "cnc_2_raw": "VARCHAR(255) NULL",
        "enc": "VARCHAR(100) NULL",
        "cliente": "VARCHAR(255) NULL",
        "ref_cliente": "VARCHAR(255) NULL",
        "processo": "VARCHAR(255) NULL",
        "artigo": "VARCHAR(255) NULL",
        "id_linha_excel": "VARCHAR(100) NULL",
        "esp_mat": "DECIMAL(12,3) NULL",
        "esp_final": "DECIMAL(12,3) NULL",
    }

    SQL_LISTAR_COLUNAS_TABELA = """
        SELECT COLUMN_NAME
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
    """

    SQL_INSERIR_OBRA = """
        INSERT INTO obras (
            codigo_obra,
            nome_obra,
            ficheiro_origem,
            folha_origem,
            observacoes
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    SQL_INSERIR_LINHA = """
        INSERT INTO linhas_obra (
            obra_id,
            numero_linha,
            linha_excel,
            estado_origem,
            nome_folha_origem,
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
            esp_final,
            dados_json
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    def preparar_estrutura_importacao(self, conexao: Any) -> None:
        """Garante os campos mínimos necessários para esta fase de importação.

        Em vez de usar `ADD COLUMN IF NOT EXISTS`, consultamos antes
        `information_schema.columns` para manter compatibilidade.
        """
        cursor = conexao.cursor()

        try:
            cursor.execute(self.SQL_CRIAR_TABELA_OBRAS)
            cursor.execute(self.SQL_CRIAR_TABELA_LINHAS_OBRA)
        finally:
            cursor.close()

        colunas_existentes = self._obter_colunas_tabela(conexao, "linhas_obra")
        cursor = conexao.cursor()

        try:
            for nome_coluna, definicao_sql in self.DEFINICOES_COLUNAS_LINHAS_OBRA.items():
                if nome_coluna in colunas_existentes:
                    continue

                sql = f"ALTER TABLE linhas_obra ADD COLUMN {nome_coluna} {definicao_sql}"
                cursor.execute(sql)
        finally:
            cursor.close()

    def inserir_obra(self, conexao: Any, obra: ObraExcel) -> int:
        """Insere uma obra e devolve o ID criado."""
        cursor = conexao.cursor()

        try:
            cursor.execute(
                self.SQL_INSERIR_OBRA,
                (
                    obra.codigo_obra,
                    obra.nome_obra,
                    obra.caminho_ficheiro,
                    "IMPORTACAO_EXCEL",
                    "Importação inicial das folhas LISTA_ORDENADA e LISTAGEM_CUT_RITE.",
                ),
            )
            return int(cursor.lastrowid)
        finally:
            cursor.close()

    def inserir_linha(self, conexao: Any, linha: LinhaObra) -> int:
        """Insere uma linha individual e devolve o ID criado."""
        cursor = conexao.cursor()

        try:
            cursor.execute(self.SQL_INSERIR_LINHA, self._linha_para_parametros(linha))
            return int(cursor.lastrowid)
        finally:
            cursor.close()

    def inserir_linhas(self, conexao: Any, linhas: list[LinhaObra]) -> int:
        """Insere várias linhas de uma só vez e devolve a quantidade inserida."""
        if not linhas:
            return 0

        cursor = conexao.cursor()

        try:
            parametros = [self._linha_para_parametros(linha) for linha in linhas]
            cursor.executemany(self.SQL_INSERIR_LINHA, parametros)
            if cursor.rowcount and cursor.rowcount > 0:
                return int(cursor.rowcount)
            return len(linhas)
        finally:
            cursor.close()

    @staticmethod
    def _linha_para_parametros(linha: LinhaObra) -> tuple[Any, ...]:
        """Converte uma linha normalizada numa tupla pronta para SQL."""
        return (
            linha.obra_id,
            linha.numero_linha,
            linha.linha_excel,
            linha.estado_origem,
            linha.nome_folha_origem,
            linha.referencia or None,
            linha.designacao or None,
            linha.descricao or None,
            linha.material or None,
            linha.comp,
            linha.larg,
            linha.esp,
            linha.qt,
            linha.veio or None,
            linha.orla_esq or None,
            linha.orla_dir or None,
            linha.orla_cima or None,
            linha.orla_baixo or None,
            linha.cnc_1_raw or None,
            linha.cnc_2_raw or None,
            linha.enc or None,
            linha.cliente or None,
            linha.ref_cliente or None,
            linha.processo or None,
            linha.artigo or None,
            linha.notas or None,
            linha.id_linha_excel or None,
            linha.esp_mat,
            linha.esp_final,
            json.dumps(linha.dados_brutos, ensure_ascii=False),
        )

    def _obter_colunas_tabela(self, conexao: Any, nome_tabela: str) -> set[str]:
        """Lê a lista de colunas já existentes numa tabela."""
        cursor = conexao.cursor()

        try:
            cursor.execute(
                self.SQL_LISTAR_COLUNAS_TABELA,
                (conexao.database, nome_tabela),
            )
            return {str(linha[0]) for linha in cursor.fetchall()}
        finally:
            cursor.close()
