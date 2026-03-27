"""Constantes centrais para ligacao e comparacao entre estados."""

from __future__ import annotations

from config.excel_mapeamentos import ESTADO_ORIGEM_FINAL, ESTADO_ORIGEM_ORIGINAL, ESTADO_ORIGEM_TRANSFORMADO


# A versao da chave identifica a logica usada nesta fase.
# A v2 separa:
# - uma chave tolerante para agrupar candidatos
# - uma assinatura forte para ligar casos equivalentes sem ambiguidade
# - um score de semelhanca para decidir pares restantes
VERSAO_CHAVE_LIGACAO = "v2"


# Campos base para agrupar candidatos de comparacao.
# Nesta v2 privilegia-se a estabilidade dos campos de texto
# mais fiaveis entre os dois estados.
CAMPOS_CHAVE_LIGACAO = (
    "descricao",
    "material",
    "artigo",
    "veio",
)


# Campos da assinatura forte.
# Quando todos estes campos coincidem apos normalizacao,
# a ligacao e considerada forte.
CAMPOS_CHAVE_FORTE = (
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


# Score minimo para aceitar uma correspondencia tolerante.
LIMIAR_SCORE_CORRESPONDENCIA_TOLERANTE = 65


# Pesos usados no score de semelhanca.
# A soma foi mantida em 100 para facilitar leitura humana.
PESOS_SCORE_CORRESPONDENCIA = {
    "descricao": 20,
    "material": 20,
    "artigo": 20,
    "veio": 5,
    "qt": 15,
    "dimensoes": 20,
}


# A estrutura ja fica preparada para futuro FINAL_VALIDADO.
# Nesta ronda comparamos apenas os dois primeiros estados.
ESTADO_COMPARACAO_BASE = ESTADO_ORIGEM_ORIGINAL
ESTADO_COMPARACAO_ALVO = ESTADO_ORIGEM_TRANSFORMADO
ESTADOS_PREPARADOS = (
    ESTADO_ORIGEM_ORIGINAL,
    ESTADO_ORIGEM_TRANSFORMADO,
    ESTADO_ORIGEM_FINAL,
)
