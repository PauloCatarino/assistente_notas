# ============================================================
# Ficheiro: testar_env.py
# Objetivo:
# Testar se o Python está a ler corretamente o ficheiro .env
# ============================================================

from pathlib import Path
import os

try:
    # Tenta importar a biblioteca que normalmente lê o .env
    from dotenv import load_dotenv
except ImportError:
    print("ERRO: a biblioteca python-dotenv não está instalada.")
    print("No terminal executa: pip install python-dotenv")
    raise

# Caminho para o ficheiro .env
caminho_env = Path(".env")

print(f"Ficheiro .env existe? {caminho_env.exists()}")

# Lê o ficheiro .env
load_dotenv(dotenv_path=caminho_env)

# Mostra os valores lidos
print("PROJECT_NAME =", os.getenv("PROJECT_NAME"))
print("APP_TESTAR_BD_NO_ARRANQUE =", os.getenv("APP_TESTAR_BD_NO_ARRANQUE"))
print("MYSQL_HOST =", os.getenv("MYSQL_HOST"))
print("MYSQL_PORT =", os.getenv("MYSQL_PORT"))
print("MYSQL_DATABASE =", os.getenv("MYSQL_DATABASE"))
print("MYSQL_USER =", os.getenv("MYSQL_USER"))

# Por segurança, não mostramos a password completa
password = os.getenv("MYSQL_PASSWORD")
if password:
    print("MYSQL_PASSWORD = [PREENCHIDA]")
else:
    print("MYSQL_PASSWORD = [VAZIA OU NÃO LIDA]")