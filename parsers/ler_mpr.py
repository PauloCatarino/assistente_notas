"""Leitura base de ficheiros CNC HOMAG em formato `.mpr`."""

from __future__ import annotations

from pathlib import Path

from models.schemas import ProgramaCNC


class LeitorMPR:
    """Lê ficheiros `.mpr` como texto simples.

    Nesta fase não existe uma interpretação profunda do formato.
    O objetivo é criar uma base estável para ler conteúdo e evoluir depois.
    """

    def __init__(self, pasta_origem: Path | None = None) -> None:
        """Guarda a pasta padrão onde os ficheiros `.mpr` poderão ser procurados."""
        self.pasta_origem = Path(pasta_origem) if pasta_origem is not None else None

    def listar_ficheiros_mpr(self) -> list[Path]:
        """Lista ficheiros `.mpr` na pasta de origem configurada."""
        if self.pasta_origem is None or not self.pasta_origem.exists():
            return []

        return sorted(
            [
                caminho
                for caminho in self.pasta_origem.iterdir()
                if caminho.is_file() and caminho.suffix.lower() == ".mpr"
            ]
        )

    def ler_texto(self, caminho_ficheiro: Path) -> str:
        """Lê o texto bruto do ficheiro `.mpr`.

        É usado `errors="ignore"` para tolerar variações de codificação
        frequentes em ficheiros exportados por software industrial.
        """
        return Path(caminho_ficheiro).read_text(encoding="utf-8", errors="ignore")

    def ler_programa(self, caminho_ficheiro: Path) -> ProgramaCNC:
        """Converte o ficheiro `.mpr` numa estrutura de dados simples."""
        conteudo = self.ler_texto(caminho_ficheiro)
        linhas = conteudo.splitlines()

        return ProgramaCNC(
            nome_programa=Path(caminho_ficheiro).stem,
            caminho_ficheiro=str(caminho_ficheiro),
            conteudo_texto=conteudo,
            total_linhas=len(linhas),
        )
