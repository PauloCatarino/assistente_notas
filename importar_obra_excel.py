"""Script simples para importar uma obra Excel para MySQL."""

from __future__ import annotations

import argparse
from pathlib import Path

from services.servico_importacao_excel import ServicoImportacaoExcel


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do script."""
    parser = argparse.ArgumentParser(
        description="Importa um ficheiro Excel IMOS para as tabelas obras e linhas_obra."
    )
    parser.add_argument(
        "--ficheiro",
        default="Lista_Material.xlsm",
        help="Caminho para o ficheiro Excel a importar.",
    )
    return parser


def main() -> int:
    """Executa a importação e mostra um resumo claro no terminal."""
    argumentos = criar_parser().parse_args()
    caminho_ficheiro = Path(argumentos.ficheiro).resolve()

    servico = ServicoImportacaoExcel()

    try:
        resultado = servico.importar_ficheiro_excel(caminho_ficheiro)
    except Exception as erro:
        print(f"Erro na importação: {erro}")
        return 1

    if resultado.duplicado_bloqueado:
        print(resultado.mensagem)
    else:
        print(f"Obra inserida: {resultado.nome_obra}")

    print(f"ID da obra: {resultado.obra_id}")

    for nome_folha, total in resultado.totais_por_folha.items():
        estado = resultado.estados_por_folha.get(nome_folha, "")
        print(f"{nome_folha} ({estado}): {total} linhas importadas")

    if resultado.avisos:
        print("Avisos:")
        for aviso in resultado.avisos:
            print(f"- {aviso}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
