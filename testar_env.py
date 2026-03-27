# ============================================================
# Ficheiro: testar_env.py
# Objetivo:
# Testar se o Python esta a ler corretamente o ficheiro .env
# ============================================================

from __future__ import annotations

import os
from pathlib import Path


def main() -> int:
    """Executa o teste simples de leitura do ficheiro .env."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("ERRO: a biblioteca python-dotenv nao esta instalada.")
        print("No terminal executa: pip install python-dotenv")
        return 1

    caminho_env = Path(".env")
    print(f"Ficheiro .env existe? {caminho_env.exists()}")

    load_dotenv(dotenv_path=caminho_env)

    print("PROJECT_NAME =", os.getenv("PROJECT_NAME"))
    print("APP_TESTAR_BD_NO_ARRANQUE =", os.getenv("APP_TESTAR_BD_NO_ARRANQUE"))
    print("MYSQL_HOST =", os.getenv("MYSQL_HOST"))
    print("MYSQL_PORT =", os.getenv("MYSQL_PORT"))
    print("MYSQL_DATABASE =", os.getenv("MYSQL_DATABASE"))
    print("MYSQL_USER =", os.getenv("MYSQL_USER"))

    password = os.getenv("MYSQL_PASSWORD")
    if password:
        print("MYSQL_PASSWORD = [PREENCHIDA]")
    else:
        print("MYSQL_PASSWORD = [VAZIA OU NAO LIDA]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
