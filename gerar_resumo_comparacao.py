"""Gera um resumo legivel da comparacao entre estados de uma obra."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from config.settings import carregar_configuracoes
from models.schemas import ResumoComparacaoEstados
from services.servico_comparacao_estados import ServicoComparacaoEstados
from services.servico_importacao_excel import ServicoImportacaoExcel


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do script."""
    parser = argparse.ArgumentParser(
        description="Gera um resumo da comparacao entre ORIGINAL_IMOS e TRANSFORMADO_AUTOMATION."
    )
    parser.add_argument(
        "--obra-id",
        type=int,
        help="ID de uma obra ja existente na base de dados.",
    )
    parser.add_argument(
        "--ficheiro",
        help="Caminho para um ficheiro Excel. Se for dado, o sistema tenta resolver a obra por importacao segura.",
    )
    parser.add_argument(
        "--gerar-csv",
        action="store_true",
        help="Gera um CSV simples com as diferencas encontradas.",
    )
    parser.add_argument(
        "--csv",
        help="Caminho opcional para o CSV. Se omitido, e usado logs/comparacao_obra_<id>.csv.",
    )
    return parser


def resolver_obra_id(obra_id: int | None, ficheiro: str | None) -> tuple[int, str]:
    """Resolve o ID da obra a partir de um argumento direto ou de um ficheiro Excel."""
    if obra_id is not None:
        return obra_id, "obra existente"

    if not ficheiro:
        raise ValueError("Indique --obra-id ou --ficheiro.")

    caminho_ficheiro = Path(ficheiro).resolve()
    servico_importacao = ServicoImportacaoExcel()
    resultado = servico_importacao.importar_ficheiro_excel(caminho_ficheiro)

    origem = "duplicado bloqueado" if resultado.duplicado_bloqueado else "obra importada"
    print(f"Importacao: {origem}.")
    print(f"obra_id resolvido: {resultado.obra_id}")

    return resultado.obra_id, resultado.nome_obra


def imprimir_resumo(resumo: ResumoComparacaoEstados, servico_comparacao: ServicoComparacaoEstados) -> None:
    """Mostra um resumo simples no terminal."""
    print("")
    print("Resumo da comparacao:")
    print(f"obra_id: {resumo.obra_id}")
    print(f"total linhas {resumo.estado_base}: {resumo.total_linhas_base}")
    print(f"total linhas {resumo.estado_alvo}: {resumo.total_linhas_alvo}")
    print(f"total chaves ligadas: {resumo.total_chaves_ligadas}")
    print(f"total pares ligados: {resumo.total_pares_ligados}")
    print(f"total linhas sem correspondencia: {resumo.total_linhas_sem_correspondencia}")
    print(f"  - sem par em {resumo.estado_base}: {resumo.total_sem_correspondencia_base}")
    print(f"  - sem par em {resumo.estado_alvo}: {resumo.total_sem_correspondencia_alvo}")
    print(f"total diferencas: {resumo.total_diferencas}")

    contagem_niveis = Counter(par.nivel_correspondencia for par in resumo.pares_correspondencia)
    if contagem_niveis:
        print("pares por nivel:")
        for nivel_correspondencia, total in sorted(contagem_niveis.items()):
            print(f"- {nivel_correspondencia}: {total}")

    top_tipos = servico_comparacao.top_tipos_diferenca(resumo)
    if top_tipos:
        print("top tipos de diferenca:")
        for tipo_diferenca, total in top_tipos:
            print(f"- {tipo_diferenca}: {total}")


def exportar_csv_diferencas(resumo: ResumoComparacaoEstados, caminho_csv: Path) -> None:
    """Exporta um CSV simples para apoiar a analise humana."""
    caminho_csv.parent.mkdir(parents=True, exist_ok=True)

    with caminho_csv.open("w", encoding="utf-8-sig", newline="") as ficheiro_csv:
        escritor = csv.writer(ficheiro_csv, delimiter=";")
        escritor.writerow(
            [
                "chave_ligacao",
                "linha_original_id",
                "linha_transformada_id",
                "tipo_diferenca",
                "campo",
                "nivel_correspondencia",
                "score_correspondencia",
                "valor_original",
                "valor_transformado",
            ]
        )

        for diferenca in resumo.diferencas:
            escritor.writerow(
                [
                    diferenca.chave_ligacao,
                    diferenca.linha_original_id or "",
                    diferenca.linha_transformada_id or "",
                    diferenca.tipo_diferenca,
                    diferenca.campo,
                    diferenca.nivel_correspondencia,
                    diferenca.score_correspondencia,
                    diferenca.valor_original or "",
                    diferenca.valor_transformado or "",
                ]
            )


def resolver_caminho_csv(argumentos: argparse.Namespace, obra_id: int) -> Path | None:
    """Resolve o caminho final do CSV, quando pedido."""
    if not argumentos.gerar_csv and not argumentos.csv:
        return None

    if argumentos.csv:
        return Path(argumentos.csv).resolve()

    configuracao = carregar_configuracoes()
    return configuracao.logs_dir / f"comparacao_obra_{obra_id}.csv"


def main() -> int:
    """Executa o resumo desta fase."""
    argumentos = criar_parser().parse_args()

    try:
        obra_id, _ = resolver_obra_id(argumentos.obra_id, argumentos.ficheiro)
    except Exception as erro:
        print(f"Erro ao resolver a obra: {erro}")
        return 1

    servico_comparacao = ServicoComparacaoEstados()

    try:
        resumo = servico_comparacao.comparar_obra(obra_id)
    except Exception as erro:
        print(f"Erro na comparacao: {erro}")
        return 1

    imprimir_resumo(resumo, servico_comparacao)

    caminho_csv = resolver_caminho_csv(argumentos, obra_id)
    if caminho_csv is not None:
        try:
            exportar_csv_diferencas(resumo, caminho_csv)
            print(f"csv gerado: {caminho_csv}")
        except Exception as erro:
            print(f"Erro a gerar CSV: {erro}")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
