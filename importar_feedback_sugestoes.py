"""Script simples para importar feedback manual de sugestoes para MySQL."""

from __future__ import annotations

import argparse
from pathlib import Path

from services.servico_sugestoes import ServicoSugestoes


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do script."""
    parser = argparse.ArgumentParser(
        description="Importa feedback manual a partir de um CSV ou Excel de validacao."
    )
    parser.add_argument(
        "--ficheiro",
        required=True,
        help="Caminho para o ficheiro CSV/XLSX de validacao preenchido.",
    )
    return parser


def main() -> int:
    """Executa a importacao do feedback e mostra um resumo simples."""
    argumentos = criar_parser().parse_args()
    caminho_ficheiro = Path(argumentos.ficheiro).resolve()

    servico = ServicoSugestoes()

    try:
        resultado = servico.importar_feedback_validacao(caminho_ficheiro)
    except Exception as erro:
        print(f"Erro na importacao do feedback: {erro}")
        return 1

    print("Resumo da importacao de feedback:")
    print(f"ficheiro: {resultado.caminho_ficheiro}")
    print(f"n de registos lidos: {resultado.total_registos_lidos}")
    print(f"n de registos importados: {resultado.total_registos_importados}")
    print(f"n de registos ignorados: {resultado.total_registos_ignorados}")
    print(f"n de duplicados ignorados: {resultado.total_registos_duplicados}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
