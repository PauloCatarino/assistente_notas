"""Servico simples para importar um ficheiro Excel para MySQL."""

from __future__ import annotations

from pathlib import Path

from config.settings import ConfiguracaoProjeto, carregar_configuracoes
from database.db_connection import GestorLigacaoMySQL
from database.repositorio_importacao_excel import RepositorioImportacaoExcel
from importers.importar_excel_cutrite import ImportadorFolhasExcel
from importers.importar_obras import ImportadorObras
from models.schemas import ResultadoImportacaoExcel


class ServicoImportacaoExcel:
    """Orquestra a leitura do Excel e a gravacao em MySQL."""

    def __init__(self, configuracao: ConfiguracaoProjeto | None = None) -> None:
        """Prepara as dependencias principais da importacao."""
        self.configuracao = configuracao or carregar_configuracoes()
        self.importador_obras = ImportadorObras(self.configuracao.excel_dir)
        self.importador_folhas = ImportadorFolhasExcel()
        self.gestor_bd = GestorLigacaoMySQL(self.configuracao)
        self.repositorio = RepositorioImportacaoExcel()

    def importar_ficheiro_excel(self, caminho_ficheiro: Path) -> ResultadoImportacaoExcel:
        """Importa uma obra Excel para MySQL e devolve um resumo simples."""
        caminho_ficheiro = Path(caminho_ficheiro).resolve()
        if not caminho_ficheiro.exists():
            raise FileNotFoundError(f"Ficheiro nao encontrado: {caminho_ficheiro}")

        obra = self.importador_obras.ler_metadados_obra(caminho_ficheiro)

        conexao = self.gestor_bd.criar_conexao()
        if conexao is None:
            raise RuntimeError(
                "Nao foi possivel criar ligacao ao MySQL. Verifique o ficheiro .env e a disponibilidade do servidor."
            )

        try:
            self.repositorio.preparar_estrutura_importacao(conexao)
            obra_existente = self.repositorio.procurar_obra_existente(conexao, obra)

            if obra_existente:
                obra_id = int(obra_existente["id"])
                self.repositorio.atualizar_metadados_obra(conexao, obra_id, obra)
                self.repositorio.sincronizar_chaves_ligacao_obra(conexao, obra_id)
                totais_por_folha, estados_por_folha = self.repositorio.obter_resumo_linhas_obra(conexao, obra_id)
                conexao.commit()

                return ResultadoImportacaoExcel(
                    nome_obra=obra.nome_obra,
                    caminho_ficheiro=obra.caminho_ficheiro,
                    obra_id=obra_id,
                    totais_por_folha=totais_por_folha,
                    estados_por_folha=estados_por_folha,
                    avisos=[],
                    duplicado_bloqueado=True,
                    mensagem="Importacao bloqueada: este ficheiro Excel ja foi importado anteriormente.",
                )

            resultados_folhas = self.importador_folhas.ler_folhas_configuradas(caminho_ficheiro)
            obra_id = self.repositorio.inserir_obra(conexao, obra)

            avisos: list[str] = []
            totais_por_folha: dict[str, int] = {}
            estados_por_folha: dict[str, str] = {}

            for resultado_folha in resultados_folhas:
                for linha in resultado_folha.linhas:
                    linha.obra_id = obra_id

                total_inserido = self.repositorio.inserir_linhas(conexao, resultado_folha.linhas)
                totais_por_folha[resultado_folha.nome_folha_real] = total_inserido
                estados_por_folha[resultado_folha.nome_folha_real] = resultado_folha.estado_origem
                avisos.extend(resultado_folha.avisos)

            self.repositorio.sincronizar_chaves_ligacao_obra(conexao, obra_id)
            conexao.commit()

            return ResultadoImportacaoExcel(
                nome_obra=obra.nome_obra,
                caminho_ficheiro=obra.caminho_ficheiro,
                obra_id=obra_id,
                totais_por_folha=totais_por_folha,
                estados_por_folha=estados_por_folha,
                avisos=avisos,
                duplicado_bloqueado=False,
                mensagem="Importacao concluida com sucesso.",
            )
        except Exception:
            conexao.rollback()
            raise
        finally:
            self.gestor_bd.fechar_conexao(conexao)
