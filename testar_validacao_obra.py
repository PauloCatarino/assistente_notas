"""Fluxo simples para preparar a validacao pratica de uma obra no Excel."""

from __future__ import annotations

import argparse
from pathlib import Path

from services.servico_sugestoes import ServicoSugestoes


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do script."""
    parser = argparse.ArgumentParser(
        description="Gera o ficheiro de validacao Excel para uma obra real."
    )
    parser.add_argument(
        "--ficheiro",
        required=True,
        help="Ficheiro Excel da obra a validar.",
    )
    parser.add_argument(
        "--gerar-csv",
        action="store_true",
        help="Gera tambem o CSV alem do Excel de validacao.",
    )
    parser.add_argument(
        "--sem-recalibracao",
        action="store_true",
        help="Usa o motor base, sem ajustes por feedback real.",
    )
    return parser


def main() -> int:
    """Executa o fluxo pratico desta fase."""
    argumentos = criar_parser().parse_args()
    caminho_ficheiro = Path(argumentos.ficheiro).resolve()

    servico = ServicoSugestoes()

    try:
        resultado = servico.analisar_ficheiro_excel(
            caminho_ficheiro,
            gerar_csv=argumentos.gerar_csv,
            gerar_excel=True,
            usar_recalibracao=not argumentos.sem_recalibracao,
        )
    except Exception as erro:
        print(f"Erro ao preparar a validacao da obra: {erro}")
        return 1

    print("Ficheiro de validacao preparado:")
    print(f"modo: {'recalibrado' if not argumentos.sem_recalibracao else 'base'}")
    print(f"obra_id: {resultado.obra_id or 'nao resolvido'}")
    print(f"excel de validacao: {resultado.caminho_excel_saida}")
    if resultado.caminho_csv_saida:
        print(f"csv de validacao: {resultado.caminho_csv_saida}")
    print(f"n de linhas analisadas: {resultado.total_linhas_analisadas}")
    print(f"n de sugestoes geradas: {resultado.total_sugestoes_geradas}")
    print("")
    print("Proximo passo:")
    print(f"1. abrir o ficheiro Excel de validacao")
    print("2. preencher as colunas `validacao_utilizador` e `nota_final_utilizador`")
    print(f"3. importar o feedback com: python importar_feedback_sugestoes.py --ficheiro \"{resultado.caminho_excel_saida}\"")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
