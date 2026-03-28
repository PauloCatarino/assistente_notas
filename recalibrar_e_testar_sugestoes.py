"""Fluxo pratico para importar feedback e comparar sugestoes antes vs depois."""

from __future__ import annotations

import argparse
from pathlib import Path

from services.servico_sugestoes import ServicoSugestoes


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do script."""
    parser = argparse.ArgumentParser(
        description="Importa feedback, recalibra o motor e compara a cobertura antes vs depois."
    )
    parser.add_argument(
        "--ficheiro-feedback",
        required=True,
        help="CSV/XLSX de validacao preenchido manualmente.",
    )
    parser.add_argument(
        "--ficheiro-excel",
        required=True,
        help="Ficheiro Excel da obra a reanalisar.",
    )
    parser.add_argument(
        "--gerar-csv",
        action="store_true",
        help="Gera tambem um CSV de validacao recalibrado.",
    )
    return parser


def main() -> int:
    """Executa o fluxo completo desta fase."""
    argumentos = criar_parser().parse_args()
    caminho_feedback = Path(argumentos.ficheiro_feedback).resolve()
    caminho_excel = Path(argumentos.ficheiro_excel).resolve()

    servico = ServicoSugestoes()

    try:
        resultado_importacao = servico.importar_feedback_validacao(caminho_feedback)
        relatorio = servico.gerar_relatorio_qualidade()

        resultado_antes = servico.analisar_ficheiro_excel(
            caminho_excel,
            gerar_csv=False,
            gerar_excel=False,
            usar_recalibracao=False,
        )

        resultado_depois = servico.analisar_ficheiro_excel(
            caminho_excel,
            caminho_csv_saida=(
                servico.configuracao.logs_dir / f"validacao_sugestoes_recalibrada_{caminho_excel.stem}.csv"
                if argumentos.gerar_csv
                else None
            ),
            caminho_excel_saida=servico.configuracao.logs_dir / f"validacao_sugestoes_recalibrada_{caminho_excel.stem}.xlsx",
            gerar_csv=argumentos.gerar_csv,
            gerar_excel=True,
            usar_recalibracao=True,
        )
    except Exception as erro:
        print(f"Erro no fluxo de recalibracao: {erro}")
        return 1

    cobertura_antes = servico._calcular_percentagem(
        resultado_antes.total_sugestoes_geradas,
        resultado_antes.total_linhas_analisadas,
    )
    cobertura_depois = servico._calcular_percentagem(
        resultado_depois.total_sugestoes_geradas,
        resultado_depois.total_linhas_analisadas,
    )

    print("Comparacao antes vs depois:")
    print(f"ficheiro feedback: {resultado_importacao.caminho_ficheiro}")
    print(f"ficheiro analisado: {resultado_depois.caminho_ficheiro}")
    print(f"n de feedbacks validos usados: {relatorio.total_linhas_analisadas}")
    print(f"n de registos ignorados por duplicacao: {resultado_importacao.total_registos_duplicados}")
    print(f"n de padroes recalibrados: {relatorio.total_padroes_recalibrados}")
    print(f"cobertura antes: {cobertura_antes}%")
    print(f"cobertura depois: {cobertura_depois}%")
    print(f"sugestoes geradas antes: {resultado_antes.total_sugestoes_geradas}")
    print(f"sugestoes geradas depois: {resultado_depois.total_sugestoes_geradas}")
    print(f"linhas sem sugestao antes: {resultado_antes.total_linhas_sem_sugestao}")
    print(f"linhas sem sugestao depois: {resultado_depois.total_linhas_sem_sugestao}")
    print(f"aceitacao antes: {relatorio.taxa_aceitacao}%")
    print(f"aceitacao depois: {relatorio.aceitacao_recalibrada_estimada}%")
    print(f"rejeicao antes: {relatorio.taxa_rejeicao}%")
    print(f"rejeicao depois: {relatorio.rejeicao_recalibrada_estimada}%")
    print(f"excel recalibrado: {resultado_depois.caminho_excel_saida}")
    if resultado_depois.caminho_csv_saida:
        print(f"csv recalibrado: {resultado_depois.caminho_csv_saida}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
