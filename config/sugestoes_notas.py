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
}
