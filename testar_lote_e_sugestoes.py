"""Script simples para testar importacao em lote e sugestoes de notas."""

from __future__ import annotations

import argparse
from pathlib import Path

from config.settings import carregar_configuracoes
from services.servico_importacao_excel import ServicoImportacaoExcel
from services.servico_sugestoes import ServicoSugestoes


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do script."""
    parser = argparse.ArgumentParser(
        description="Importa ficheiros .xlsm em lote e gera sugestoes para um ficheiro especifico."
    )
    parser.add_argument(
        "--pasta",
        help="Pasta onde estao os ficheiros .xlsm. Se omitido, usa a pasta do projeto.",
    )
    parser.add_argument(
        "--ficheiro",
        required=True,
        help="Ficheiro Excel especifico a analisar apos a importacao em lote.",
    )
    parser.add_argument(
        "--csv",
        help="Caminho opcional para o CSV de validacao.",
    )
    parser.add_argument(
        "--xlsx",
        help="Caminho opcional para o Excel de validacao.",
    )
    return parser


def main() -> int:
    """Executa o fluxo simples desta fase."""
    argumentos = criar_parser().parse_args()
    configuracao = carregar_configuracoes()
    pasta_origem = Path(argumentos.pasta).resolve() if argumentos.pasta else configuracao.base_dir
    caminho_ficheiro = Path(argumentos.ficheiro).resolve()
    caminho_csv = Path(argumentos.csv).resolve() if argumentos.csv else None
    caminho_excel = Path(argumentos.xlsx).resolve() if argumentos.xlsx else None

    servico_importacao = ServicoImportacaoExcel(configuracao)
    servico_sugestoes = ServicoSugestoes(configuracao)

    try:
        resultado_lote = servico_importacao.importar_pasta_excel(pasta_origem)
    except Exception as erro:
        print(f"Erro na importacao em lote: {erro}")
        return 1

    print("Resumo da importacao em lote:")
    print(f"n de ficheiros encontrados: {resultado_lote.total_ficheiros_encontrados}")
    print(f"n de ficheiros importados: {resultado_lote.total_ficheiros_importados}")
    print(f"n de duplicados ignorados: {resultado_lote.total_duplicados_ignorados}")

    if resultado_lote.totais_linhas_por_estado:
        print("linhas importadas por estado:")
        for estado_origem, total_linhas in sorted(resultado_lote.totais_linhas_por_estado.items()):
            print(f"- {estado_origem}: {total_linhas}")

    if resultado_lote.erros:
        print("Erros encontrados na importacao:")
        for erro in resultado_lote.erros:
            print(f"- {erro}")

    try:
        resultado_sugestoes = servico_sugestoes.analisar_ficheiro_excel(
            caminho_ficheiro,
            caminho_csv_saida=caminho_csv,
            caminho_excel_saida=caminho_excel,
            gerar_csv=bool(argumentos.csv),
            gerar_excel=True,
        )
    except Exception as erro:
        print(f"Erro na analise de sugestoes: {erro}")
        return 1

    print("")
    print("Resumo das sugestoes:")
    print(f"n de obras no historico: {resultado_sugestoes.total_obras_historico}")
    print(f"n de linhas com nota historica: {resultado_sugestoes.total_linhas_com_nota_historica}")
    print(f"n de sugestoes geradas: {resultado_sugestoes.total_sugestoes_geradas}")
    print(f"n de linhas sem sugestao: {resultado_sugestoes.total_linhas_sem_sugestao}")
    print(f"excel de validacao: {resultado_sugestoes.caminho_excel_saida}")
    if resultado_sugestoes.caminho_csv_saida:
        print(f"csv de validacao: {resultado_sugestoes.caminho_csv_saida}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
