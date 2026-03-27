"""Configuração central do projeto."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    # `python-dotenv` é opcional em tempo de importação.
    # Se não existir ainda, o projeto continua a arrancar com as variáveis do sistema.
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - caminho simples de fallback
    load_dotenv = None


def _texto_para_bool(valor: str | None, valor_por_omissao: bool = False) -> bool:
    """Converte texto de ambiente para booleano de forma previsível."""
    if valor is None:
        return valor_por_omissao

    return valor.strip().lower() in {"1", "true", "sim", "yes", "y"}


@dataclass(slots=True)
class ConfiguracaoProjeto:
    """Estrutura simples com toda a configuração usada pelo projeto."""

    project_name: str
    base_dir: Path
    data_dir: Path
    excel_dir: Path
    mpr_dir: Path
    logs_dir: Path
    mysql_host: str
    mysql_port: int
    mysql_database: str
    mysql_user: str
    mysql_password: str
    testar_bd_no_arranque: bool
    folha_excel_original: str = "LISTA_ORDENADA"
    folha_excel_processada: str = "LISTAGEM_CUT_RITE"


def carregar_configuracoes() -> ConfiguracaoProjeto:
    """Carrega a configuração do projeto a partir do `.env` e do sistema."""
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / ".env"

    if load_dotenv is not None and env_path.exists():
        load_dotenv(env_path)

    data_dir = base_dir / os.getenv("DATA_DIR", "data")
    excel_dir = base_dir / os.getenv("EXCEL_DIR", "data/excel")
    mpr_dir = base_dir / os.getenv("MPR_DIR", "data/mpr")
    logs_dir = base_dir / os.getenv("LOGS_DIR", "logs")

    return ConfiguracaoProjeto(
        project_name=os.getenv("PROJECT_NAME", "assistente_notas"),
        base_dir=base_dir,
        data_dir=data_dir,
        excel_dir=excel_dir,
        mpr_dir=mpr_dir,
        logs_dir=logs_dir,
        mysql_host=os.getenv("MYSQL_HOST", "localhost"),
        mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
        mysql_database=os.getenv("MYSQL_DATABASE", "assistente_notas"),
        mysql_user=os.getenv("MYSQL_USER", "root"),
        mysql_password=os.getenv("MYSQL_PASSWORD", ""),
        testar_bd_no_arranque=_texto_para_bool(
            os.getenv("APP_TESTAR_BD_NO_ARRANQUE"),
            valor_por_omissao=False,
        ),
    )
