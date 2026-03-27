"""Script simples para testar duplicados e comparacao entre estados."""

from __future__ import annotations

import argparse
from pathlib import Path

from services.servico_comparacao_estados import ServicoComparacaoEstados
from services.servico_importacao_excel import ServicoImportacaoExcel


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do script."""
    parser = argparse.ArgumentParser(
        description="Testa bloqueio de duplicados e a primeira comparacao entre estados."
    )
    parser.add_argument(
        "--ficheiro",
        default="Lista_Material.xlsm",
        help="Caminho para o ficheiro Excel a testar.",
    )
    return parser


def main() -> int:
    """Executa o teste desta fase e mostra um resumo claro."""
    argumentos = criar_parser().parse_args()
    caminho_ficheiro = Path(argumentos.ficheiro).resolve()

    servico_importacao = ServicoImportacaoExcel()
    servico_comparacao = ServicoComparacaoEstados()

    try:
        resultado_importacao = servico_importacao.importar_ficheiro_excel(caminho_ficheiro)
    except Exception as erro:
        print(f"Erro no teste da importacao: {erro}")
        return 1

    print("Resultado da importacao:")
    print(f"obra_id: {resultado_importacao.obra_id}")
    print(f"duplicado bloqueado: {'sim' if resultado_importacao.duplicado_bloqueado else 'nao'}")
    print(f"mensagem: {resultado_importacao.mensagem}")

    for nome_folha, total in resultado_importacao.totais_por_folha.items():
        estado = resultado_importacao.estados_por_folha.get(nome_folha, "")
        print(f"{nome_folha} ({estado}): {total} linhas")

    try:
        resumo = servico_comparacao.comparar_obra(resultado_importacao.obra_id)
    except Exception as erro:
        print(f"Erro na comparacao de estados: {erro}")
        return 1

    print("")
    print("Resultado da comparacao:")
    print(f"obra_id: {resumo.obra_id}")
    print(f"linhas {resumo.estado_base}: {resumo.total_linhas_base}")
    print(f"linhas {resumo.estado_alvo}: {resumo.total_linhas_alvo}")
    print(f"n de chaves ligadas: {resumo.total_chaves_ligadas}")
    print(f"n de pares ligados: {resumo.total_pares_ligados}")
    print(f"n de diferencas encontradas: {resumo.total_diferencas}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
