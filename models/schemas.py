"""Estruturas de dados simples usadas pelo projeto."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ObraExcel:
    """Representa um ficheiro Excel tratado como uma obra."""

    codigo_obra: str | None
    nome_obra: str
    caminho_ficheiro: str
    folhas_disponiveis: list[str] = field(default_factory=list)
    nome_ficheiro: str = ""
    hash_ficheiro: str = ""
    tamanho_ficheiro: int | None = None
    data_ficheiro: datetime | None = None

    def para_dict(self) -> dict[str, Any]:
        """Converte a instancia para dicionario."""
        return asdict(self)


@dataclass(slots=True)
class LinhaObra:
    """Representa uma linha preparada para insercao na tabela `linhas_obra`."""

    obra_id: int | None
    estado_origem: str
    nome_folha_origem: str
    linha_excel: int
    id: int | None = None
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
    chave_ligacao: str = ""
    dados_brutos: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Preenche campos derivados simples para manter compatibilidade."""
        if self.numero_linha is None:
            self.numero_linha = self.linha_excel

        if not self.designacao:
            self.designacao = self.descricao

        if not self.chave_ligacao:
            self.chave_ligacao = self.gerar_chave_ligacao()

    def gerar_chave_ligacao(self) -> str:
        """Calcula a versao atual da chave de ligacao."""
        from utils.chave_ligacao import gerar_chave_ligacao_linha

        return gerar_chave_ligacao_linha(self)

    def gerar_assinatura_forte(self) -> str:
        """Calcula a assinatura forte da linha."""
        from utils.chave_ligacao import gerar_assinatura_forte_linha

        return gerar_assinatura_forte_linha(self)

    def para_dict(self) -> dict[str, Any]:
        """Converte a instancia para dicionario."""
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
        """Devolve o numero total de linhas lidas."""
        return len(self.linhas)


@dataclass(slots=True)
class ResultadoImportacaoExcel:
    """Resumo simples da importacao completa de um ficheiro Excel."""

    nome_obra: str
    caminho_ficheiro: str
    obra_id: int
    totais_por_folha: dict[str, int] = field(default_factory=dict)
    estados_por_folha: dict[str, str] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)
    duplicado_bloqueado: bool = False
    mensagem: str = ""

    def para_dict(self) -> dict[str, Any]:
        """Converte a instancia para dicionario."""
        return asdict(self)


@dataclass(slots=True)
class ParCorrespondencia:
    """Representa um par ligado entre estados."""

    obra_id: int
    chave_ligacao: str
    linha_original_id: int | None
    linha_transformada_id: int | None
    nivel_correspondencia: str
    score_correspondencia: int

    def para_dict(self) -> dict[str, Any]:
        """Converte a instancia para dicionario."""
        return asdict(self)


@dataclass(slots=True)
class DiferencaEstado:
    """Representa uma diferenca encontrada entre dois estados."""

    obra_id: int
    chave_ligacao: str
    linha_original_id: int | None
    linha_transformada_id: int | None
    campo: str
    valor_original: str | None
    valor_transformado: str | None
    tipo_diferenca: str
    nivel_correspondencia: str = ""
    score_correspondencia: int = 0

    def para_dict(self) -> dict[str, Any]:
        """Converte a instancia para dicionario."""
        return asdict(self)


@dataclass(slots=True)
class ResumoComparacaoEstados:
    """Resumo simples da comparacao entre estados."""

    obra_id: int
    estado_base: str
    estado_alvo: str
    total_linhas_base: int
    total_linhas_alvo: int
    total_chaves_ligadas: int
    total_pares_ligados: int
    total_sem_correspondencia_base: int
    total_sem_correspondencia_alvo: int
    total_linhas_sem_correspondencia: int
    total_diferencas: int
    pares_correspondencia: list[ParCorrespondencia] = field(default_factory=list)
    diferencas: list[DiferencaEstado] = field(default_factory=list)

    def para_dict(self) -> dict[str, Any]:
        """Converte a instancia para dicionario."""
        return asdict(self)


@dataclass(slots=True)
class ProgramaCNC:
    """Representa um programa CNC lido de um ficheiro `.mpr`."""

    nome_programa: str
    caminho_ficheiro: str
    conteudo_texto: str | None = None
    total_linhas: int = 0

    def para_dict(self) -> dict[str, Any]:
        """Converte a instancia para dicionario."""
        return asdict(self)


@dataclass(slots=True)
class TokenCNC:
    """Representa um token encontrado num programa CNC."""

    cnc_programa_id: int | None
    token: str
    ocorrencias: int = 1
    origem: str | None = None

    def para_dict(self) -> dict[str, Any]:
        """Converte a instancia para dicionario."""
        return asdict(self)


@dataclass(slots=True)
class SugestaoNotaLog:
    """Representa um registo simples de sugestao de nota."""

    linha_obra_id: int | None
    sugestao_texto: str | None
    nota_original: str
    origem_sugestao: str
    confianca: float | None
    estado: str
    detalhes_json: dict[str, Any] = field(default_factory=dict)
    criado_em: str = ""

    def para_dict(self) -> dict[str, Any]:
        """Converte a instancia para dicionario."""
        return asdict(self)
