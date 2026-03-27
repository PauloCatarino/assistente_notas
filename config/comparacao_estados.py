"""Constantes centrais para ligacao e comparacao entre estados."""

from __future__ import annotations

from config.excel_mapeamentos import ESTADO_ORIGEM_FINAL, ESTADO_ORIGEM_ORIGINAL, ESTADO_ORIGEM_TRANSFORMADO


# Esta versao identifica a primeira formula simples da chave.
# Mantemos um prefixo de versao para permitir evolucao futura
# sem perder clareza sobre como a chave foi gerada.
VERSAO_CHAVE_LIGACAO = "v1"


# Primeira versao da chave de ligacao.
# Nesta fase usamos uma combinacao simples e estavel de campos.
# A ideia e ligar linhas equivalentes entre estados, nao resolver
# todos os casos complexos logo no inicio.
CAMPOS_CHAVE_LIGACAO = (
    "descricao",
    "material",
    "comp",
    "larg",
    "qt",
    "artigo",
    "veio",
)


# Campos minimos comparados nesta fase.
CAMPOS_COMPARACAO_ESTADOS = (
    "descricao",
    "material",
    "comp",
    "larg",
    "qt",
    "artigo",
    "notas",
    "esp",
    "orla_esq",
    "orla_dir",
    "orla_cima",
    "orla_baixo",
    "cnc_1_raw",
    "cnc_2_raw",
)


# A estrutura ja fica preparada para futuro FINAL_VALIDADO.
# Nesta ronda comparamos apenas os dois primeiros estados.
ESTADO_COMPARACAO_BASE = ESTADO_ORIGEM_ORIGINAL
ESTADO_COMPARACAO_ALVO = ESTADO_ORIGEM_TRANSFORMADO
ESTADOS_PREPARADOS = (
    ESTADO_ORIGEM_ORIGINAL,
    ESTADO_ORIGEM_TRANSFORMADO,
    ESTADO_ORIGEM_FINAL,
)
