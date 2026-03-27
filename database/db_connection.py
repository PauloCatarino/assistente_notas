"""Ligação simples ao MySQL."""

from __future__ import annotations

from typing import Any

from config.settings import ConfiguracaoProjeto

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:  # pragma: no cover - fallback simples para arranque sem dependências
    mysql = None
    Error = Exception


class GestorLigacaoMySQL:
    """Encapsula a criação e validação da ligação ao MySQL.

    Motivo da existência desta classe:
    concentrar o código de acesso à base de dados num único ponto, para que
    os restantes módulos não precisem de conhecer detalhes de ligação.
    """

    def __init__(self, configuracao: ConfiguracaoProjeto) -> None:
        """Guarda a configuração necessária para criar ligações futuras."""
        self.configuracao = configuracao

    def criar_conexao(self) -> Any | None:
        """Cria uma ligação MySQL e devolve o objeto de conexão."""
        if mysql is None:
            print("Dependência em falta: instalar `mysql-connector-python`.")
            return None

        try:
            return mysql.connector.connect(
                host=self.configuracao.mysql_host,
                port=self.configuracao.mysql_port,
                database=self.configuracao.mysql_database,
                user=self.configuracao.mysql_user,
                password=self.configuracao.mysql_password,
            )
        except Error as erro:
            print(f"Erro ao ligar ao MySQL: {erro}")
            return None

    def testar_conexao(self) -> bool:
        """Testa a ligação à base de dados e fecha-a de seguida."""
        conexao = self.criar_conexao()
        if conexao is None:
            return False

        try:
            return bool(conexao.is_connected())
        finally:
            self.fechar_conexao(conexao)

    @staticmethod
    def fechar_conexao(conexao: Any | None) -> None:
        """Fecha a conexão se ela existir e estiver ativa."""
        if conexao is None:
            return

        try:
            if conexao.is_connected():
                conexao.close()
        except Exception as erro:  # pragma: no cover - proteção defensiva
            print(f"Aviso ao fechar ligação MySQL: {erro}")
