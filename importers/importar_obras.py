"""Leitura inicial de obras a partir de ficheiros Excel."""

from __future__ import annotations

from pathlib import Path

from models.schemas import ObraExcel

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover - fallback simples
    load_workbook = None


class ImportadorObras:
    """Responsável por localizar ficheiros Excel e ler os seus metadados básicos."""

    EXTENSOES_VALIDAS = {".xlsx", ".xlsm", ".xls"}

    def __init__(self, pasta_origem: Path) -> None:
        """Guarda a pasta onde os ficheiros Excel serão procurados."""
        self.pasta_origem = Path(pasta_origem)

    def listar_ficheiros_excel(self) -> list[Path]:
        """Lista ficheiros Excel suportados dentro da pasta configurada."""
        if not self.pasta_origem.exists():
            return []

        return sorted(
            [
                caminho
                for caminho in self.pasta_origem.iterdir()
                if caminho.is_file() and caminho.suffix.lower() in self.EXTENSOES_VALIDAS
            ]
        )

    def ler_metadados_obra(self, caminho_ficheiro: Path) -> ObraExcel:
        """Lê informação simples do ficheiro para representar uma obra.

        Nesta fase, o nome da obra é derivado do nome do ficheiro.
        Esta decisão é simples, previsível e suficiente para arrancar.
        """
        if load_workbook is None:
            raise RuntimeError("Instale `openpyxl` para ler ficheiros Excel.")

        workbook = load_workbook(filename=caminho_ficheiro, read_only=True, data_only=True)
        try:
            folhas_disponiveis = list(workbook.sheetnames)
        finally:
            workbook.close()

        return ObraExcel(
            codigo_obra=caminho_ficheiro.stem,
            nome_obra=caminho_ficheiro.stem,
            caminho_ficheiro=str(caminho_ficheiro),
            folhas_disponiveis=folhas_disponiveis,
        )

    def importar_pasta(self) -> list[ObraExcel]:
        """Importa os metadados básicos de todos os ficheiros Excel encontrados."""
        obras: list[ObraExcel] = []

        for caminho_ficheiro in self.listar_ficheiros_excel():
            try:
                obras.append(self.ler_metadados_obra(caminho_ficheiro))
            except Exception as erro:
                print(f"Erro ao ler obra '{caminho_ficheiro.name}': {erro}")

        return obras
