"""Mapeamentos centrais de folhas e colunas Excel."""

from __future__ import annotations

from dataclasses import dataclass

from utils.helpers import normalizar_texto_chave


ESTADO_ORIGEM_ORIGINAL = "ORIGINAL_IMOS"
ESTADO_ORIGEM_TRANSFORMADO = "TRANSFORMADO_AUTOMATION"
ESTADO_ORIGEM_FINAL = "FINAL_VALIDADO"


@dataclass(frozen=True, slots=True)
class ConfiguracaoFolhaExcel:
    """Define como uma folha Excel deve ser lida e mapeada."""

    nome_logico: str
    nomes_folha_aceites: tuple[str, ...]
    estado_origem: str
    colunas_excel_para_campo: dict[str, str]
    linha_procura_cabecalho_maxima: int = 10

    def mapa_colunas_normalizado(self) -> dict[str, str]:
        """Devolve o mapa com cabeçalhos já normalizados."""
        return {
            normalizar_texto_chave(nome_excel): campo
            for nome_excel, campo in self.colunas_excel_para_campo.items()
        }


COLUNAS_IGNORADAS_EXCEL = (
    "Orla",
    "Grafico Orlas",
    "+comp",
    "+Larg",
    "Tipo_Lacagem",
    "Notas_1",
    "Cliente_Final",
    "CNC",
    "ABD",
    "BHT",
)


CONFIG_LISTA_ORDENADA = ConfiguracaoFolhaExcel(
    nome_logico="LISTA_ORDENADA",
    nomes_folha_aceites=("LISTA_ORDENADA", "lista_ordenada"),
    estado_origem=ESTADO_ORIGEM_ORIGINAL,
    colunas_excel_para_campo={
        "Descricao": "descricao",
        "Material": "material",
        "Comp.": "comp",
        "Larg.": "larg",
        "Esp": "esp",
        "Qt.": "qt",
        "Veio": "veio",
        "Orla ESQ": "orla_esq",
        "Orla DIR": "orla_dir",
        "Orla CIMA": "orla_cima",
        "Orla BAIXO": "orla_baixo",
        "CNC_1": "cnc_1_raw",
        "CNC_2": "cnc_2_raw",
        "Enc.": "enc",
        "Cliente": "cliente",
        "Artigo": "artigo",
        "Notas": "notas",
    },
)


CONFIG_LISTAGEM_CUT_RITE = ConfiguracaoFolhaExcel(
    nome_logico="LISTAGEM_CUT_RITE",
    nomes_folha_aceites=("LISTAGEM_CUT_RITE",),
    estado_origem=ESTADO_ORIGEM_TRANSFORMADO,
    colunas_excel_para_campo={
        "Descricao": "descricao",
        "Material": "material",
        "Comp": "comp",
        "Larg": "larg",
        "Qt": "qt",
        "Veio": "veio",
        "Cliente": "cliente",
        "Ref_Cliente": "ref_cliente",
        "Processo": "processo",
        "Artigo": "artigo",
        "Notas": "notas",
        "Esp": "esp",
        "Orla ESQ": "orla_esq",
        "Orla DIR": "orla_dir",
        "Orla CIMA": "orla_cima",
        "Orla BAIXO": "orla_baixo",
        "ID": "id_linha_excel",
        "CNC_1": "cnc_1_raw",
        "CNC_2": "cnc_2_raw",
        "Esp.Mat": "esp_mat",
        "Esp.Final": "esp_final",
    },
)


FOLHAS_IMPORTACAO_EXCEL = (
    CONFIG_LISTA_ORDENADA,
    CONFIG_LISTAGEM_CUT_RITE,
)


def obter_configuracao_folha(nome_folha: str) -> ConfiguracaoFolhaExcel | None:
    """Procura a configuração de uma folha a partir do seu nome."""
    nome_folha_normalizado = normalizar_texto_chave(nome_folha)

    for configuracao in FOLHAS_IMPORTACAO_EXCEL:
        nomes_aceites = {
            normalizar_texto_chave(nome)
            for nome in configuracao.nomes_folha_aceites
        }
        if nome_folha_normalizado in nomes_aceites:
            return configuracao

    return None
