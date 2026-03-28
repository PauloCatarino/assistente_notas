"""Script simples para relatorio de qualidade das sugestoes."""

from __future__ import annotations

import argparse

from services.servico_sugestoes import ServicoSugestoes


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do script."""
    parser = argparse.ArgumentParser(
        description="Gera um relatorio simples da qualidade das sugestoes com base no feedback."
    )
    parser.add_argument(
        "--obra-id",
        type=int,
        help="Filtra o relatorio para uma obra especifica.",
    )
    return parser


def _imprimir_topicos(titulo: str, itens: list[tuple[str, int]]) -> None:
    """Mostra uma lista curta de top padrões."""
    print(titulo)
    if not itens:
        print("- sem dados")
        return

    for texto, total in itens:
        print(f"- {texto}: {total}")


def main() -> int:
    """Executa o relatorio de qualidade."""
    argumentos = criar_parser().parse_args()
    servico = ServicoSugestoes()

    try:
        relatorio = servico.gerar_relatorio_qualidade(obra_id=argumentos.obra_id)
    except Exception as erro:
        print(f"Erro ao gerar relatorio de qualidade: {erro}")
        return 1

    print("Relatorio de qualidade:")
    print(f"total de linhas analisadas: {relatorio.total_linhas_analisadas}")
    print(f"total de linhas com sugestao: {relatorio.total_linhas_com_sugestao}")
    print(f"total de linhas sem sugestao: {relatorio.total_linhas_sem_sugestao}")
    print(f"total de sugestoes aceites: {relatorio.total_sugestoes_aceites}")
    print(f"total de sugestoes rejeitadas: {relatorio.total_sugestoes_rejeitadas}")
    print(f"total de sugestoes editadas: {relatorio.total_sugestoes_editadas}")
    print(f"taxa de cobertura: {relatorio.taxa_cobertura}%")
    print(f"taxa de aceitacao: {relatorio.taxa_aceitacao}%")
    print(f"taxa de rejeicao: {relatorio.taxa_rejeicao}%")
    _imprimir_topicos("descricoes com mais acertos:", relatorio.top_descricoes_com_mais_acertos)
    _imprimir_topicos("descricoes com mais falhas:", relatorio.top_descricoes_com_mais_falhas)
    _imprimir_topicos("notas mais aceites:", relatorio.top_notas_mais_aceites)
    _imprimir_topicos("notas mais rejeitadas:", relatorio.top_notas_mais_rejeitadas)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
