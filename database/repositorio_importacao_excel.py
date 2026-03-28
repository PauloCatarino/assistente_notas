"""Persistencia simples para importacao Excel -> MySQL."""

from __future__ import annotations

import json
from typing import Any

from models.schemas import LinhaObra, ObraExcel


class RepositorioImportacaoExcel:
    """Concentra as operacoes de base de dados usadas nesta fase do projeto."""

    SQL_CRIAR_TABELA_OBRAS = """
        CREATE TABLE IF NOT EXISTS obras (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            codigo_obra VARCHAR(100) NULL,
            nome_obra VARCHAR(255) NOT NULL,
            nome_ficheiro VARCHAR(255) NULL,
            nome_base VARCHAR(150) NULL,
            referencia_obra VARCHAR(150) NULL,
            num_encomenda_phc VARCHAR(50) NULL,
            versao_obra VARCHAR(20) NULL,
            ano_obra VARCHAR(20) NULL,
            cliente_codigo VARCHAR(100) NULL,
            ficheiro_origem VARCHAR(500) NOT NULL,
            hash_ficheiro VARCHAR(64) NULL,
            tamanho_ficheiro BIGINT NULL,
            data_ficheiro DATETIME NULL,
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
            chave_ligacao VARCHAR(64) NULL,
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

    DEFINICOES_COLUNAS_OBRAS = {
        "nome_ficheiro": "VARCHAR(255) NULL",
        "nome_base": "VARCHAR(150) NULL",
        "referencia_obra": "VARCHAR(150) NULL",
        "num_encomenda_phc": "VARCHAR(50) NULL",
        "versao_obra": "VARCHAR(20) NULL",
        "ano_obra": "VARCHAR(20) NULL",
        "cliente_codigo": "VARCHAR(100) NULL",
        "hash_ficheiro": "VARCHAR(64) NULL",
        "tamanho_ficheiro": "BIGINT NULL",
        "data_ficheiro": "DATETIME NULL",
    }

    DEFINICOES_COLUNAS_LINHAS_OBRA = {
        "linha_excel": "INT NULL",
        "estado_origem": "VARCHAR(50) NULL",
        "nome_folha_origem": "VARCHAR(100) NULL",
        "chave_ligacao": "VARCHAR(64) NULL",
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
            nome_ficheiro,
            nome_base,
            referencia_obra,
            num_encomenda_phc,
            versao_obra,
            ano_obra,
            cliente_codigo,
            ficheiro_origem,
            hash_ficheiro,
            tamanho_ficheiro,
            data_ficheiro,
            folha_origem,
            observacoes
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    SQL_ATUALIZAR_METADADOS_OBRA = """
        UPDATE obras
        SET
            nome_ficheiro = %s,
            nome_base = %s,
            referencia_obra = %s,
            num_encomenda_phc = %s,
            versao_obra = %s,
            ano_obra = %s,
            cliente_codigo = %s,
            ficheiro_origem = %s,
            hash_ficheiro = %s,
            tamanho_ficheiro = %s,
            data_ficheiro = %s
        WHERE id = %s
    """

    SQL_BUSCAR_OBRA_POR_HASH = """
        SELECT *
        FROM obras
        WHERE hash_ficheiro = %s
        ORDER BY id
        LIMIT 1
    """

    SQL_BUSCAR_OBRA_POR_CAMINHO = """
        SELECT *
        FROM obras
        WHERE ficheiro_origem = %s
          AND (hash_ficheiro IS NULL OR hash_ficheiro = '')
        ORDER BY id
        LIMIT 1
    """

    SQL_BUSCAR_OBRA_POR_NOME_E_TAMANHO = """
        SELECT *
        FROM obras
        WHERE nome_ficheiro = %s
          AND nome_obra = %s
          AND tamanho_ficheiro = %s
          AND (hash_ficheiro IS NULL OR hash_ficheiro = '')
        ORDER BY id
        LIMIT 1
    """

    SQL_INSERIR_LINHA = """
        INSERT INTO linhas_obra (
            obra_id,
            numero_linha,
            linha_excel,
            estado_origem,
            nome_folha_origem,
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
            esp_final,
            dados_json
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s
        )
    """

    SQL_OBTER_RESUMO_LINHAS_OBRA = """
        SELECT nome_folha_origem, estado_origem, COUNT(*) AS total
        FROM linhas_obra
        WHERE obra_id = %s
        GROUP BY nome_folha_origem, estado_origem
        ORDER BY nome_folha_origem
    """

    SQL_OBTER_LINHAS_PARA_CHAVE = """
        SELECT
            id,
            obra_id,
            estado_origem,
            nome_folha_origem,
            linha_excel,
            numero_linha,
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
            chave_ligacao
        FROM linhas_obra
        WHERE obra_id = %s
        ORDER BY estado_origem, linha_excel, id
    """

    SQL_ATUALIZAR_CHAVE_LIGACAO = """
        UPDATE linhas_obra
        SET chave_ligacao = %s
        WHERE id = %s
    """

    def preparar_estrutura_importacao(self, conexao: Any) -> None:
        """Garante as tabelas e colunas minimas desta fase."""
        cursor = conexao.cursor()

        try:
            cursor.execute(self.SQL_CRIAR_TABELA_OBRAS)
            cursor.execute(self.SQL_CRIAR_TABELA_LINHAS_OBRA)
        finally:
            cursor.close()

        self._garantir_colunas_tabela(conexao, "obras", self.DEFINICOES_COLUNAS_OBRAS)
        self._garantir_colunas_tabela(conexao, "linhas_obra", self.DEFINICOES_COLUNAS_LINHAS_OBRA)

    def procurar_obra_existente(self, conexao: Any, obra: ObraExcel) -> dict[str, Any] | None:
        """Procura se o ficheiro ja foi importado."""
        cursor = conexao.cursor(dictionary=True)

        try:
            if obra.hash_ficheiro:
                cursor.execute(self.SQL_BUSCAR_OBRA_POR_HASH, (obra.hash_ficheiro,))
                registo = cursor.fetchone()
                if registo:
                    return registo

            cursor.execute(self.SQL_BUSCAR_OBRA_POR_CAMINHO, (obra.caminho_ficheiro,))
            registo = cursor.fetchone()
            if registo:
                return registo

            if obra.nome_ficheiro and obra.tamanho_ficheiro is not None:
                cursor.execute(
                    self.SQL_BUSCAR_OBRA_POR_NOME_E_TAMANHO,
                    (obra.nome_ficheiro, obra.nome_obra, obra.tamanho_ficheiro),
                )
                return cursor.fetchone()

            return None
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
                    obra.nome_ficheiro or None,
                    obra.nome_base or None,
                    obra.referencia_obra or None,
                    obra.num_encomenda_phc or None,
                    obra.versao_obra or None,
                    obra.ano_obra or None,
                    obra.cliente_codigo or None,
                    obra.caminho_ficheiro,
                    obra.hash_ficheiro or None,
                    obra.tamanho_ficheiro,
                    obra.data_ficheiro,
                    "IMPORTACAO_EXCEL",
                    "Importacao dos estados ORIGINAL_IMOS e TRANSFORMADO_AUTOMATION.",
                ),
            )
            return int(cursor.lastrowid)
        finally:
            cursor.close()

    def atualizar_metadados_obra(self, conexao: Any, obra_id: int, obra: ObraExcel) -> None:
        """Atualiza os metadados tecnicos de uma obra existente."""
        cursor = conexao.cursor()

        try:
            cursor.execute(
                self.SQL_ATUALIZAR_METADADOS_OBRA,
                (
                    obra.nome_ficheiro or None,
                    obra.nome_base or None,
                    obra.referencia_obra or None,
                    obra.num_encomenda_phc or None,
                    obra.versao_obra or None,
                    obra.ano_obra or None,
                    obra.cliente_codigo or None,
                    obra.caminho_ficheiro,
                    obra.hash_ficheiro or None,
                    obra.tamanho_ficheiro,
                    obra.data_ficheiro,
                    obra_id,
                ),
            )
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
        """Insere varias linhas de uma so vez e devolve a quantidade inserida."""
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

    def obter_resumo_linhas_obra(
        self,
        conexao: Any,
        obra_id: int,
    ) -> tuple[dict[str, int], dict[str, str]]:
        """Devolve totais por folha e os respetivos estados."""
        cursor = conexao.cursor(dictionary=True)

        try:
            cursor.execute(self.SQL_OBTER_RESUMO_LINHAS_OBRA, (obra_id,))
            totais_por_folha: dict[str, int] = {}
            estados_por_folha: dict[str, str] = {}

            for linha in cursor.fetchall():
                nome_folha = str(linha["nome_folha_origem"])
                totais_por_folha[nome_folha] = int(linha["total"])
                estados_por_folha[nome_folha] = str(linha["estado_origem"])

            return totais_por_folha, estados_por_folha
        finally:
            cursor.close()

    def sincronizar_chaves_ligacao_obra(self, conexao: Any, obra_id: int) -> int:
        """Recalcula e grava as chaves de ligacao de todas as linhas da obra."""
        cursor = conexao.cursor(dictionary=True)

        try:
            cursor.execute(self.SQL_OBTER_LINHAS_PARA_CHAVE, (obra_id,))
            registos = cursor.fetchall()
        finally:
            cursor.close()

        atualizacoes: list[tuple[str, int]] = []

        for registo in registos:
            linha = LinhaObra(
                id=int(registo["id"]),
                obra_id=registo["obra_id"],
                estado_origem=str(registo["estado_origem"]),
                nome_folha_origem=str(registo["nome_folha_origem"]),
                linha_excel=int(registo["linha_excel"]),
                numero_linha=int(registo["numero_linha"]),
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
                chave_ligacao=str(registo["chave_ligacao"] or ""),
            )

            nova_chave = linha.gerar_chave_ligacao()
            if nova_chave != str(registo["chave_ligacao"] or ""):
                atualizacoes.append((nova_chave, int(registo["id"])))

        if not atualizacoes:
            return 0

        cursor = conexao.cursor()
        try:
            cursor.executemany(self.SQL_ATUALIZAR_CHAVE_LIGACAO, atualizacoes)
            if cursor.rowcount and cursor.rowcount > 0:
                return int(cursor.rowcount)
            return len(atualizacoes)
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
            linha.chave_ligacao or None,
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

    def _garantir_colunas_tabela(
        self,
        conexao: Any,
        nome_tabela: str,
        definicoes_colunas: dict[str, str],
    ) -> None:
        """Garante as colunas minimas de uma tabela."""
        colunas_existentes = self._obter_colunas_tabela(conexao, nome_tabela)
        cursor = conexao.cursor()

        try:
            for nome_coluna, definicao_sql in definicoes_colunas.items():
                if nome_coluna in colunas_existentes:
                    continue

                sql = f"ALTER TABLE {nome_tabela} ADD COLUMN {nome_coluna} {definicao_sql}"
                try:
                    cursor.execute(sql)
                except Exception as erro:
                    mensagem_erro = str(erro)
                    if "Duplicate column name" in mensagem_erro:
                        continue
                    raise
        finally:
            cursor.close()

    def _obter_colunas_tabela(self, conexao: Any, nome_tabela: str) -> set[str]:
        """Le a lista de colunas ja existentes numa tabela."""
        cursor = conexao.cursor()

        try:
            cursor.execute(
                self.SQL_LISTAR_COLUNAS_TABELA,
                (conexao.database, nome_tabela),
            )
            return {str(linha[0]) for linha in cursor.fetchall()}
        finally:
            cursor.close()
