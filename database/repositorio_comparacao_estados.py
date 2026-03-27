"""Persistencia simples para comparacao entre estados."""

from __future__ import annotations

from typing import Any

from models.schemas import DiferencaEstado, LinhaObra


class RepositorioComparacaoEstados:
    """Concentra as operacoes de comparacao e diferencas entre estados."""

    SQL_CRIAR_TABELA_DIFERENCAS = """
        CREATE TABLE IF NOT EXISTS diferencas_estados (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            obra_id BIGINT NOT NULL,
            chave_ligacao VARCHAR(64) NOT NULL,
            linha_original_id BIGINT NULL,
            linha_transformada_id BIGINT NULL,
            campo VARCHAR(100) NOT NULL,
            valor_original TEXT NULL,
            valor_transformado TEXT NULL,
            tipo_diferenca VARCHAR(50) NOT NULL,
            nivel_correspondencia VARCHAR(20) NULL,
            score_correspondencia INT NULL,
            criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """

    DEFINICOES_COLUNAS_DIFERENCAS = {
        "nivel_correspondencia": "VARCHAR(20) NULL",
        "score_correspondencia": "INT NULL",
    }

    SQL_LISTAR_COLUNAS_TABELA = """
        SELECT COLUMN_NAME
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
    """

    SQL_LIMPAR_DIFERENCAS_OBRA = """
        DELETE FROM diferencas_estados
        WHERE obra_id = %s
    """

    SQL_INSERIR_DIFERENCA = """
        INSERT INTO diferencas_estados (
            obra_id,
            chave_ligacao,
            linha_original_id,
            linha_transformada_id,
            campo,
            valor_original,
            valor_transformado,
            tipo_diferenca,
            nivel_correspondencia,
            score_correspondencia
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    SQL_OBTER_LINHAS_POR_ESTADO = """
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
        WHERE obra_id = %s
          AND estado_origem = %s
        ORDER BY chave_ligacao, linha_excel, id
    """

    def preparar_estrutura_comparacao(self, conexao: Any) -> None:
        """Garante a existencia da tabela de diferencas."""
        cursor = conexao.cursor()

        try:
            cursor.execute(self.SQL_CRIAR_TABELA_DIFERENCAS)
        finally:
            cursor.close()

        self._garantir_colunas_tabela(conexao, "diferencas_estados", self.DEFINICOES_COLUNAS_DIFERENCAS)

    def limpar_diferencas_obra(self, conexao: Any, obra_id: int) -> None:
        """Remove diferencas anteriores da obra antes de recalcular."""
        cursor = conexao.cursor()

        try:
            cursor.execute(self.SQL_LIMPAR_DIFERENCAS_OBRA, (obra_id,))
        finally:
            cursor.close()

    def guardar_diferencas(self, conexao: Any, diferencas: list[DiferencaEstado]) -> int:
        """Guarda as diferencas encontradas."""
        if not diferencas:
            return 0

        cursor = conexao.cursor()

        try:
            parametros = [
                (
                    diferenca.obra_id,
                    diferenca.chave_ligacao,
                    diferenca.linha_original_id,
                    diferenca.linha_transformada_id,
                    diferenca.campo,
                    diferenca.valor_original,
                    diferenca.valor_transformado,
                    diferenca.tipo_diferenca,
                    diferenca.nivel_correspondencia or None,
                    diferenca.score_correspondencia,
                )
                for diferenca in diferencas
            ]
            cursor.executemany(self.SQL_INSERIR_DIFERENCA, parametros)
            if cursor.rowcount and cursor.rowcount > 0:
                return int(cursor.rowcount)
            return len(diferencas)
        finally:
            cursor.close()

    def obter_linhas_por_estado(self, conexao: Any, obra_id: int, estado_origem: str) -> list[LinhaObra]:
        """Le as linhas de uma obra para um estado especifico."""
        cursor = conexao.cursor(dictionary=True)

        try:
            cursor.execute(self.SQL_OBTER_LINHAS_POR_ESTADO, (obra_id, estado_origem))
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
                    if "Duplicate column name" in str(erro):
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
