# ============================================================
# Ficheiro: testar_mysql.py
# Objetivo:
# Testar ligacao direta ao MySQL usando os dados do .env
# ============================================================

from __future__ import annotations

import os
from pathlib import Path


def main() -> int:
    """Executa o teste de ligacao direta ao MySQL."""
    from dotenv import load_dotenv

    load_dotenv(Path(".env"))

    try:
        import mysql.connector
    except ImportError:
        print("ERRO: falta instalar mysql-connector-python")
        print("No terminal executa:")
        print("pip install mysql-connector-python")
        return 1

    try:
        ligacao = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            database=os.getenv("MYSQL_DATABASE"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
        )

        if ligacao.is_connected():
            print("Ligacao MySQL: OK")
            print("Base de dados:", os.getenv("MYSQL_DATABASE"))

        ligacao.close()
        return 0
    except Exception as erro:
        print("Ligacao MySQL: FALHOU")
        print("Erro encontrado:")
        print(erro)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
