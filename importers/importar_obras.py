"""Leitura inicial de obras a partir de ficheiros Excel."""

from __future__ import annotations

from pathlib import Path

from models.schemas import ObraExcel
from utils.helpers import calcular_hash_ficheiro, obter_metadados_ficheiro

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover - fallback simples
    load_workbook = None


class ImportadorObras:
    """Responsavel por localizar ficheiros Excel e ler os seus metadados basicos."""

    EXTENSOES_VALIDAS = {".xlsx", ".xlsm", ".xls"}

    def __init__(self, pasta_origem: Path) -> None:
        """Guarda a pasta onde os ficheiros Excel serao procurados."""
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
        """Le informacao simples do ficheiro para representar uma obra.

        Nesta fase, o nome da obra e derivado do nome do ficheiro.
        Tambem recolhemos metadados tecnicos para bloquear duplicados.
        """
        if load_workbook is None:
            raise RuntimeError("Instale `openpyxl` para ler ficheiros Excel.")

        caminho_ficheiro = Path(caminho_ficheiro).resolve()
        nome_ficheiro, tamanho_ficheiro, data_ficheiro = obter_metadados_ficheiro(caminho_ficheiro)
        hash_ficheiro = calcular_hash_ficheiro(caminho_ficheiro)

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
            nome_ficheiro=nome_ficheiro,
            hash_ficheiro=hash_ficheiro,
            tamanho_ficheiro=tamanho_ficheiro,
            data_ficheiro=data_ficheiro,
        )

    def importar_pasta(self) -> list[ObraExcel]:
        """Importa os metadados basicos de todos os ficheiros Excel encontrados."""
        obras: list[ObraExcel] = []

        for caminho_ficheiro in self.listar_ficheiros_excel():
            try:
                obras.append(self.ler_metadados_obra(caminho_ficheiro))
            except Exception as erro:
                print(f"Erro ao ler obra '{caminho_ficheiro.name}': {erro}")

        return obras
