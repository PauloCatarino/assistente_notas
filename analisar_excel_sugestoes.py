"""Script simples para gerar ficheiros de validacao de sugestoes."""

from __future__ import annotations

import argparse
from pathlib import Path

from services.servico_sugestoes import ServicoSugestoes


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do script."""
    parser = argparse.ArgumentParser(
        description="Analisa um ficheiro Excel e gera ficheiros de validacao das sugestoes."
    )
    parser.add_argument(
        "--ficheiro",
        required=True,
        help="Caminho para o ficheiro Excel a analisar.",
    )
    parser.add_argument(
        "--csv",
        help="Caminho opcional para o CSV de validacao.",
    )
    parser.add_argument(
        "--xlsx",
        help="Caminho opcional para o Excel de validacao.",
    )
    parser.add_argument(
        "--gerar-csv",
        action="store_true",
        help="Gera tambem o CSV alem do ficheiro Excel.",
    )
    parser.add_argument(
        "--sem-excel",
        action="store_true",
        help="Nao gera o ficheiro Excel de validacao.",
    )
    return parser


def main() -> int:
    """Executa a analise e mostra um resumo simples."""
    argumentos = criar_parser().parse_args()
    caminho_ficheiro = Path(argumentos.ficheiro).resolve()
    caminho_csv = Path(argumentos.csv).resolve() if argumentos.csv else None
    caminho_excel = Path(argumentos.xlsx).resolve() if argumentos.xlsx else None

    servico = ServicoSugestoes()

    try:
        resultado = servico.analisar_ficheiro_excel(
            caminho_ficheiro,
            caminho_csv_saida=caminho_csv,
            caminho_excel_saida=caminho_excel,
            gerar_csv=argumentos.gerar_csv or bool(argumentos.csv),
            gerar_excel=not argumentos.sem_excel,
        )
    except Exception as erro:
        print(f"Erro na analise de sugestoes: {erro}")
        return 1

    print("Resumo da analise:")
    print(f"ficheiro: {resultado.caminho_ficheiro}")
    print(f"folha analisada: {resultado.nome_folha_analisada}")
    print(f"obra_id: {resultado.obra_id or 'nao resolvido'}")
    print(f"n de obras no historico: {resultado.total_obras_historico}")
    print(f"n de linhas com nota historica: {resultado.total_linhas_com_nota_historica}")
    print(f"n de linhas analisadas: {resultado.total_linhas_analisadas}")
    print(f"n de sugestoes geradas: {resultado.total_sugestoes_geradas}")
    print(f"n de linhas sem sugestao: {resultado.total_linhas_sem_sugestao}")

    if resultado.caminho_excel_saida:
        print(f"excel de validacao: {resultado.caminho_excel_saida}")
    if resultado.caminho_csv_saida:
        print(f"csv de validacao: {resultado.caminho_csv_saida}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
