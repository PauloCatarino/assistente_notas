# ============================================================
# Ficheiro: testar_mysql.py
# Objetivo:
# Testar ligação direta ao MySQL usando os dados do .env
# ============================================================

from pathlib import Path
import os

from dotenv import load_dotenv

# Lê o ficheiro .env
load_dotenv(Path(".env"))

# Tenta usar mysql-connector-python
try:
    import mysql.connector
except ImportError:
    print("ERRO: falta instalar mysql-connector-python")
    print("No terminal executa:")
    print("pip install mysql-connector-python")
    raise

try:
    ligacao = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
    )

    if ligacao.is_connected():
        print("Ligação MySQL: OK")
        print("Base de dados:", os.getenv("MYSQL_DATABASE"))

    ligacao.close()

except Exception as erro:
    print("Ligação MySQL: FALHOU")
    print("Erro encontrado:")
    print(erro)