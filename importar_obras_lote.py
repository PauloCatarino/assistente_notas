"""Script simples para importar em lote varios ficheiros Excel de uma pasta."""

from __future__ import annotations

import argparse
from pathlib import Path

from config.settings import carregar_configuracoes
from services.servico_importacao_excel import ServicoImportacaoExcel


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do script."""
    parser = argparse.ArgumentParser(
        description="Importa em lote ficheiros .xlsm de uma pasta para MySQL."
    )
    parser.add_argument(
        "--pasta",
        help="Pasta a analisar. Se omitido, usa a pasta do projeto.",
    )
    return parser


def main() -> int:
    """Executa a importacao em lote e mostra um resumo simples."""
    argumentos = criar_parser().parse_args()
    configuracao = carregar_configuracoes()
    pasta_origem = Path(argumentos.pasta).resolve() if argumentos.pasta else configuracao.base_dir

    servico = ServicoImportacaoExcel(configuracao)

    try:
        resultado = servico.importar_pasta_excel(pasta_origem)
    except Exception as erro:
        print(f"Erro na importacao em lote: {erro}")
        return 1

    print("Resumo da importacao em lote:")
    print(f"pasta analisada: {resultado.pasta_origem}")
    print(f"n de ficheiros encontrados: {resultado.total_ficheiros_encontrados}")
    print(f"n de ficheiros importados: {resultado.total_ficheiros_importados}")
    print(f"n de duplicados ignorados: {resultado.total_duplicados_ignorados}")
    print(f"n de erros: {resultado.total_erros}")

    if resultado.totais_linhas_por_estado:
        print("linhas importadas por estado:")
        for estado_origem, total_linhas in sorted(resultado.totais_linhas_por_estado.items()):
            print(f"- {estado_origem}: {total_linhas}")

    if resultado.erros:
        print("Erros encontrados:")
        for erro in resultado.erros:
            print(f"- {erro}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
