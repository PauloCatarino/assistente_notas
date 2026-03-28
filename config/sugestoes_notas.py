"""Constantes centrais para sugestoes e validacao manual em Excel."""

from __future__ import annotations


COLUNAS_EXPORTACAO_VALIDACAO = (
    "obra_id",
    "linha_excel",
    "descricao",
    "material",
    "artigo",
    "notas_atual",
    "sugestao_1",
    "score_1",
    "sugestao_2",
    "score_2",
    "justificacao",
    "validacao_utilizador",
    "nota_final_utilizador",
)


VALIDACOES_ACEITES = {
    "aceite",
    "aceita",
    "aceitar",
    "aceite sugestao 1",
    "sim",
    "s",
    "ok",
    "correta",
    "correto",
}


VALIDACOES_REJEITADAS = {
    "rejeitada",
    "rejeitado",
    "rejeitar",
    "nao aceite",
    "nao aceita",
    "nao sugerir",
    "nao",
    "n",
    "errada",
    "errado",
}


VALIDACOES_EDITADAS = {
    "editada",
    "editado",
    "editar",
    "ajustada",
    "ajustado",
    "parcial",
    "aceite sugestao 2",
}


# Score minimo para um historico entrar como candidato.
LIMIAR_CANDIDATO = 45


# Limiar base usado no motor antigo.
LIMIAR_SUGESTAO_BASE = 65


# Limiar mais exigente usado quando a recalibracao esta ativa.
LIMIAR_SUGESTAO_RECALIBRADA = 78


# Minimos de respostas para confiar em ajustes por feedback.
MIN_RESPOSTAS_RECALIBRAR_NOTA = 3
MIN_RESPOSTAS_RECALIBRAR_DESCRICAO_NOTA = 2


# Limites de seguranca para nao exagerar os ajustes.
AJUSTE_MAXIMO_POSITIVO = 18
AJUSTE_MAXIMO_NEGATIVO = -30
