"""Ponto de entrada simples para arrancar o projeto."""

from __future__ import annotations

from config.settings import carregar_configuracoes
from database.db_connection import GestorLigacaoMySQL
from importers.importar_obras import ImportadorObras
from parsers.ler_mpr import LeitorMPR
from services.servico_sugestoes import ServicoSugestoes
from utils.helpers import garantir_pastas


def main() -> int:
    """Arranca o projeto com uma validação básica do ambiente."""
    configuracao = carregar_configuracoes()

    # Garante que as pastas principais existem, mesmo num arranque limpo.
    garantir_pastas(
        [
            configuracao.data_dir,
            configuracao.excel_dir,
            configuracao.mpr_dir,
            configuracao.logs_dir,
        ]
    )

    print(f"Projeto: {configuracao.project_name}")
    print(f"Pasta base: {configuracao.base_dir}")

    importador_obras = ImportadorObras(configuracao.excel_dir)
    leitor_mpr = LeitorMPR(configuracao.mpr_dir)
    servico_sugestoes = ServicoSugestoes(configuracao.logs_dir)

    ficheiros_excel = importador_obras.listar_ficheiros_excel()
    ficheiros_mpr = leitor_mpr.listar_ficheiros_mpr()

    print(f"Ficheiros Excel encontrados: {len(ficheiros_excel)}")
    print(f"Ficheiros MPR encontrados: {len(ficheiros_mpr)}")
    print(f"Log de sugestões: {servico_sugestoes.caminho_log}")

    if configuracao.testar_bd_no_arranque:
        gestor_bd = GestorLigacaoMySQL(configuracao)
        if gestor_bd.testar_conexao():
            print("Ligação MySQL: OK")
        else:
            print("Ligação MySQL: falhou")
    else:
        print("Ligação MySQL: teste desativado no .env")

    print("Arranque concluído.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
