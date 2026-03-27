"""Estruturas de dados simples usadas pelo projeto."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ObraExcel:
    """Representa um ficheiro Excel tratado como uma obra."""

    codigo_obra: str | None
    nome_obra: str
    caminho_ficheiro: str
    folhas_disponiveis: list[str] = field(default_factory=list)

    def para_dict(self) -> dict[str, Any]:
        """Converte a instância para dicionário."""
        return asdict(self)


@dataclass(slots=True)
class LinhaObra:
    """Representa uma linha preparada para inserção na tabela `linhas_obra`."""

    obra_id: int | None
    estado_origem: str
    nome_folha_origem: str
    linha_excel: int
    numero_linha: int | None = None
    referencia: str = ""
    designacao: str = ""
    descricao: str = ""
    material: str = ""
    comp: float | None = None
    larg: float | None = None
    esp: float | None = None
    qt: float | None = None
    veio: str = ""
    orla_esq: str = ""
    orla_dir: str = ""
    orla_cima: str = ""
    orla_baixo: str = ""
    cnc_1_raw: str = ""
    cnc_2_raw: str = ""
    enc: str = ""
    cliente: str = ""
    ref_cliente: str = ""
    processo: str = ""
    artigo: str = ""
    notas: str = ""
    id_linha_excel: str = ""
    esp_mat: float | None = None
    esp_final: float | None = None
    dados_brutos: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Preenche campos derivados simples para manter compatibilidade."""
        if self.numero_linha is None:
            self.numero_linha = self.linha_excel

        if not self.designacao:
            self.designacao = self.descricao

    def para_dict(self) -> dict[str, Any]:
        """Converte a instância para dicionário."""
        return asdict(self)


@dataclass(slots=True)
class ResultadoLeituraFolhaExcel:
    """Agrupa as linhas lidas e os avisos gerados para uma folha."""

    nome_folha_esperada: str
    nome_folha_real: str
    estado_origem: str
    linha_cabecalho: int
    colunas_mapeadas: dict[str, str] = field(default_factory=dict)
    linhas: list[LinhaObra] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def total_linhas(self) -> int:
        """Devolve o número total de linhas lidas."""
        return len(self.linhas)


@dataclass(slots=True)
class ResultadoImportacaoExcel:
    """Resumo simples da importação completa de um ficheiro Excel."""

    nome_obra: str
    caminho_ficheiro: str
    obra_id: int
    totais_por_folha: dict[str, int] = field(default_factory=dict)
    estados_por_folha: dict[str, str] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)

    def para_dict(self) -> dict[str, Any]:
        """Converte a instância para dicionário."""
        return asdict(self)


@dataclass(slots=True)
class ProgramaCNC:
    """Representa um programa CNC lido de um ficheiro `.mpr`."""

    nome_programa: str
    caminho_ficheiro: str
    conteudo_texto: str | None = None
    total_linhas: int = 0

    def para_dict(self) -> dict[str, Any]:
        """Converte a instância para dicionário."""
        return asdict(self)


@dataclass(slots=True)
class TokenCNC:
    """Representa um token encontrado num programa CNC."""

    cnc_programa_id: int | None
    token: str
    ocorrencias: int = 1
    origem: str | None = None

    def para_dict(self) -> dict[str, Any]:
        """Converte a instância para dicionário."""
        return asdict(self)


@dataclass(slots=True)
class SugestaoNotaLog:
    """Representa um registo simples de sugestão de nota."""

    linha_obra_id: int | None
    sugestao_texto: str | None
    nota_original: str
    origem_sugestao: str
    confianca: float | None
    estado: str
    detalhes_json: dict[str, Any] = field(default_factory=dict)
    criado_em: str = ""

    def para_dict(self) -> dict[str, Any]:
        """Converte a instância para dicionário."""
        return asdict(self)
