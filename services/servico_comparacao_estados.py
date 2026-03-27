"""Servico simples para comparar ORIGINAL_IMOS e TRANSFORMADO_AUTOMATION."""

from __future__ import annotations

from collections import defaultdict
from itertools import zip_longest

from config.comparacao_estados import CAMPOS_COMPARACAO_ESTADOS, ESTADO_COMPARACAO_ALVO, ESTADO_COMPARACAO_BASE
from config.settings import ConfiguracaoProjeto, carregar_configuracoes
from database.db_connection import GestorLigacaoMySQL
from database.repositorio_comparacao_estados import RepositorioComparacaoEstados
from database.repositorio_importacao_excel import RepositorioImportacaoExcel
from models.schemas import DiferencaEstado, LinhaObra, ResumoComparacaoEstados
from utils.chave_ligacao import normalizar_valor_para_comparacao, valor_para_texto_legivel


class ServicoComparacaoEstados:
    """Gera a primeira comparacao estruturada entre estados de uma obra."""

    def __init__(self, configuracao: ConfiguracaoProjeto | None = None) -> None:
        """Prepara dependencias de comparacao e persistencia."""
        self.configuracao = configuracao or carregar_configuracoes()
        self.gestor_bd = GestorLigacaoMySQL(self.configuracao)
        self.repositorio_importacao = RepositorioImportacaoExcel()
        self.repositorio_comparacao = RepositorioComparacaoEstados()

    def comparar_obra(
        self,
        obra_id: int,
        estado_base: str = ESTADO_COMPARACAO_BASE,
        estado_alvo: str = ESTADO_COMPARACAO_ALVO,
        guardar_em_bd: bool = True,
    ) -> ResumoComparacaoEstados:
        """Compara dois estados da mesma obra e devolve um resumo simples."""
        conexao = self.gestor_bd.criar_conexao()
        if conexao is None:
            raise RuntimeError("Nao foi possivel criar ligacao ao MySQL para a comparacao.")

        try:
            self.repositorio_importacao.preparar_estrutura_importacao(conexao)
            self.repositorio_comparacao.preparar_estrutura_comparacao(conexao)
            self.repositorio_importacao.sincronizar_chaves_ligacao_obra(conexao, obra_id)

            linhas_base = self.repositorio_comparacao.obter_linhas_por_estado(conexao, obra_id, estado_base)
            linhas_alvo = self.repositorio_comparacao.obter_linhas_por_estado(conexao, obra_id, estado_alvo)

            resumo = self.comparar_linhas_em_memoria(
                obra_id=obra_id,
                linhas_base=linhas_base,
                linhas_alvo=linhas_alvo,
                estado_base=estado_base,
                estado_alvo=estado_alvo,
            )

            if guardar_em_bd:
                self.repositorio_comparacao.limpar_diferencas_obra(conexao, obra_id)
                self.repositorio_comparacao.guardar_diferencas(conexao, resumo.diferencas)

            conexao.commit()
            return resumo
        except Exception:
            conexao.rollback()
            raise
        finally:
            self.gestor_bd.fechar_conexao(conexao)

    def comparar_linhas_em_memoria(
        self,
        obra_id: int,
        linhas_base: list[LinhaObra],
        linhas_alvo: list[LinhaObra],
        estado_base: str,
        estado_alvo: str,
    ) -> ResumoComparacaoEstados:
        """Compara duas listas de linhas ja lidas.

        A estrategia desta fase e simples:
        1. agrupar por `chave_ligacao`
        2. ordenar por `linha_excel`
        3. ligar pares por posicao dentro da mesma chave

        Esta primeira versao privilegia clareza e previsibilidade.
        """
        grupos_base = self._agrupar_por_chave(linhas_base)
        grupos_alvo = self._agrupar_por_chave(linhas_alvo)

        chaves_base = set(grupos_base.keys())
        chaves_alvo = set(grupos_alvo.keys())
        chaves_todas = sorted(chaves_base.union(chaves_alvo))
        total_chaves_ligadas = len(chaves_base.intersection(chaves_alvo))

        diferencas: list[DiferencaEstado] = []
        total_pares_ligados = 0

        for chave_ligacao in chaves_todas:
            grupo_base = grupos_base.get(chave_ligacao, [])
            grupo_alvo = grupos_alvo.get(chave_ligacao, [])

            for linha_base, linha_alvo in zip_longest(grupo_base, grupo_alvo):
                if linha_base is not None and linha_alvo is not None:
                    total_pares_ligados += 1
                    diferencas.extend(
                        self._comparar_par_linhas(
                            obra_id=obra_id,
                            chave_ligacao=chave_ligacao,
                            linha_base=linha_base,
                            linha_alvo=linha_alvo,
                        )
                    )
                    continue

                if linha_base is not None:
                    diferencas.append(
                        DiferencaEstado(
                            obra_id=obra_id,
                            chave_ligacao=chave_ligacao,
                            linha_original_id=linha_base.id,
                            linha_transformada_id=None,
                            campo="linha",
                            valor_original=f"linha_excel={linha_base.linha_excel}",
                            valor_transformado=None,
                            tipo_diferenca="AUSENTE_NO_TRANSFORMADO",
                        )
                    )
                    continue

                if linha_alvo is not None:
                    diferencas.append(
                        DiferencaEstado(
                            obra_id=obra_id,
                            chave_ligacao=chave_ligacao,
                            linha_original_id=None,
                            linha_transformada_id=linha_alvo.id,
                            campo="linha",
                            valor_original=None,
                            valor_transformado=f"linha_excel={linha_alvo.linha_excel}",
                            tipo_diferenca="AUSENTE_NO_ORIGINAL",
                        )
                    )

        return ResumoComparacaoEstados(
            obra_id=obra_id,
            estado_base=estado_base,
            estado_alvo=estado_alvo,
            total_linhas_base=len(linhas_base),
            total_linhas_alvo=len(linhas_alvo),
            total_chaves_ligadas=total_chaves_ligadas,
            total_pares_ligados=total_pares_ligados,
            total_diferencas=len(diferencas),
            diferencas=diferencas,
        )

    def _comparar_par_linhas(
        self,
        obra_id: int,
        chave_ligacao: str,
        linha_base: LinhaObra,
        linha_alvo: LinhaObra,
    ) -> list[DiferencaEstado]:
        """Compara dois registos ligados pela mesma chave."""
        diferencas: list[DiferencaEstado] = []

        for campo in CAMPOS_COMPARACAO_ESTADOS:
            valor_base = getattr(linha_base, campo, None)
            valor_alvo = getattr(linha_alvo, campo, None)

            if normalizar_valor_para_comparacao(campo, valor_base) == normalizar_valor_para_comparacao(campo, valor_alvo):
                continue

            diferencas.append(
                DiferencaEstado(
                    obra_id=obra_id,
                    chave_ligacao=chave_ligacao,
                    linha_original_id=linha_base.id,
                    linha_transformada_id=linha_alvo.id,
                    campo=campo,
                    valor_original=valor_para_texto_legivel(valor_base),
                    valor_transformado=valor_para_texto_legivel(valor_alvo),
                    tipo_diferenca="VALOR_ALTERADO",
                )
            )

        return diferencas

    @staticmethod
    def _agrupar_por_chave(linhas: list[LinhaObra]) -> dict[str, list[LinhaObra]]:
        """Agrupa linhas por chave e ordena cada grupo por linha_excel."""
        grupos: dict[str, list[LinhaObra]] = defaultdict(list)

        for linha in linhas:
            chave_ligacao = linha.chave_ligacao or linha.gerar_chave_ligacao()
            if not chave_ligacao:
                chave_ligacao = f"SEM_CHAVE_{linha.estado_origem}_{linha.id or linha.linha_excel}"

            grupos[chave_ligacao].append(linha)

        for chave_ligacao in grupos:
            grupos[chave_ligacao].sort(key=lambda linha: (linha.linha_excel, linha.id or 0))

        return dict(grupos)
