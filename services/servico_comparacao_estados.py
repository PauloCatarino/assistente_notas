"""Servico simples para comparar ORIGINAL_IMOS e TRANSFORMADO_AUTOMATION."""

from __future__ import annotations

from collections import Counter, defaultdict

from config.comparacao_estados import CAMPOS_COMPARACAO_ESTADOS, ESTADO_COMPARACAO_ALVO, ESTADO_COMPARACAO_BASE
from config.settings import ConfiguracaoProjeto, carregar_configuracoes
from database.db_connection import GestorLigacaoMySQL
from database.repositorio_comparacao_estados import RepositorioComparacaoEstados
from database.repositorio_importacao_excel import RepositorioImportacaoExcel
from models.schemas import DiferencaEstado, LinhaObra, ParCorrespondencia, ResumoComparacaoEstados
from utils.chave_ligacao import (
    aceitar_correspondencia_tolerante,
    calcular_score_correspondencia,
    classificar_nivel_correspondencia,
    normalizar_valor_para_comparacao,
    valor_para_texto_legivel,
)


class ServicoComparacaoEstados:
    """Gera a comparacao estruturada entre estados de uma obra."""

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

        Estrategia v2:
        1. agrupar por `chave_ligacao` tolerante
        2. ligar primeiro pares com assinatura forte identica
        3. ligar os restantes por score de semelhanca
        4. considerar sem par tudo o que sobrar
        """
        grupos_base = self._agrupar_por_chave(linhas_base)
        grupos_alvo = self._agrupar_por_chave(linhas_alvo)

        chaves_base = set(grupos_base.keys())
        chaves_alvo = set(grupos_alvo.keys())
        chaves_todas = sorted(chaves_base.union(chaves_alvo))
        total_chaves_ligadas = len(chaves_base.intersection(chaves_alvo))

        pares_correspondencia: list[ParCorrespondencia] = []
        diferencas: list[DiferencaEstado] = []
        total_sem_correspondencia_base = 0
        total_sem_correspondencia_alvo = 0

        for chave_ligacao in chaves_todas:
            grupo_base = grupos_base.get(chave_ligacao, [])
            grupo_alvo = grupos_alvo.get(chave_ligacao, [])

            pares_grupo, diferencas_grupo, sem_par_base, sem_par_alvo = self._ligar_grupo_por_niveis(
                obra_id=obra_id,
                chave_ligacao=chave_ligacao,
                grupo_base=grupo_base,
                grupo_alvo=grupo_alvo,
            )

            pares_correspondencia.extend(pares_grupo)
            diferencas.extend(diferencas_grupo)
            total_sem_correspondencia_base += sem_par_base
            total_sem_correspondencia_alvo += sem_par_alvo

        total_pares_ligados = len(pares_correspondencia)
        total_linhas_sem_correspondencia = total_sem_correspondencia_base + total_sem_correspondencia_alvo

        return ResumoComparacaoEstados(
            obra_id=obra_id,
            estado_base=estado_base,
            estado_alvo=estado_alvo,
            total_linhas_base=len(linhas_base),
            total_linhas_alvo=len(linhas_alvo),
            total_chaves_ligadas=total_chaves_ligadas,
            total_pares_ligados=total_pares_ligados,
            total_sem_correspondencia_base=total_sem_correspondencia_base,
            total_sem_correspondencia_alvo=total_sem_correspondencia_alvo,
            total_linhas_sem_correspondencia=total_linhas_sem_correspondencia,
            total_diferencas=len(diferencas),
            pares_correspondencia=pares_correspondencia,
            diferencas=diferencas,
        )

    def _ligar_grupo_por_niveis(
        self,
        obra_id: int,
        chave_ligacao: str,
        grupo_base: list[LinhaObra],
        grupo_alvo: list[LinhaObra],
    ) -> tuple[list[ParCorrespondencia], list[DiferencaEstado], int, int]:
        """Liga um grupo usando correspondencia forte e depois tolerante."""
        pares: list[ParCorrespondencia] = []
        diferencas: list[DiferencaEstado] = []

        usados_base: set[int] = set()
        usados_alvo: set[int] = set()

        # Nivel 1: pares fortes dentro da mesma chave tolerante.
        base_por_assinatura = self._agrupar_por_assinatura_forte(grupo_base)
        alvo_por_assinatura = self._agrupar_por_assinatura_forte(grupo_alvo)

        for assinatura_forte in sorted(set(base_por_assinatura.keys()).intersection(alvo_por_assinatura.keys())):
            linhas_base = base_por_assinatura[assinatura_forte]
            linhas_alvo = alvo_por_assinatura[assinatura_forte]

            for linha_base, linha_alvo in zip(linhas_base, linhas_alvo):
                usados_base.add(id(linha_base))
                usados_alvo.add(id(linha_alvo))
                par = ParCorrespondencia(
                    obra_id=obra_id,
                    chave_ligacao=chave_ligacao,
                    linha_original_id=linha_base.id,
                    linha_transformada_id=linha_alvo.id,
                    nivel_correspondencia=classificar_nivel_correspondencia(100, assinatura_forte_igual=True),
                    score_correspondencia=100,
                )
                pares.append(par)
                diferencas.extend(self._comparar_par_linhas(obra_id, chave_ligacao, linha_base, linha_alvo, par))

        # Nivel 2: pares tolerantes por score.
        restantes_base = [linha for linha in grupo_base if id(linha) not in usados_base]
        restantes_alvo = [linha for linha in grupo_alvo if id(linha) not in usados_alvo]
        candidatos: list[tuple[int, LinhaObra, LinhaObra]] = []

        for linha_base in restantes_base:
            for linha_alvo in restantes_alvo:
                score_correspondencia = calcular_score_correspondencia(linha_base, linha_alvo)
                if not aceitar_correspondencia_tolerante(score_correspondencia):
                    continue
                candidatos.append((score_correspondencia, linha_base, linha_alvo))

        candidatos.sort(
            key=lambda item: (
                -item[0],
                item[1].linha_excel,
                item[2].linha_excel,
                item[1].id or 0,
                item[2].id or 0,
            )
        )

        for score_correspondencia, linha_base, linha_alvo in candidatos:
            if id(linha_base) in usados_base or id(linha_alvo) in usados_alvo:
                continue

            usados_base.add(id(linha_base))
            usados_alvo.add(id(linha_alvo))
            par = ParCorrespondencia(
                obra_id=obra_id,
                chave_ligacao=chave_ligacao,
                linha_original_id=linha_base.id,
                linha_transformada_id=linha_alvo.id,
                nivel_correspondencia=classificar_nivel_correspondencia(
                    score_correspondencia,
                    assinatura_forte_igual=False,
                ),
                score_correspondencia=score_correspondencia,
            )
            pares.append(par)
            diferencas.extend(self._comparar_par_linhas(obra_id, chave_ligacao, linha_base, linha_alvo, par))

        # Nivel 3: o que sobra fica sem par.
        sem_par_base = [linha for linha in grupo_base if id(linha) not in usados_base]
        sem_par_alvo = [linha for linha in grupo_alvo if id(linha) not in usados_alvo]

        for linha_base in sem_par_base:
            diferencas.append(
                DiferencaEstado(
                    obra_id=obra_id,
                    chave_ligacao=chave_ligacao,
                    linha_original_id=linha_base.id,
                    linha_transformada_id=None,
                    campo="linha",
                    valor_original=f"linha_excel={linha_base.linha_excel}",
                    valor_transformado=None,
                    tipo_diferenca="LINHA_SEM_PAR",
                    nivel_correspondencia="SEM_PAR",
                    score_correspondencia=0,
                )
            )

        for linha_alvo in sem_par_alvo:
            diferencas.append(
                DiferencaEstado(
                    obra_id=obra_id,
                    chave_ligacao=chave_ligacao,
                    linha_original_id=None,
                    linha_transformada_id=linha_alvo.id,
                    campo="linha",
                    valor_original=None,
                    valor_transformado=f"linha_excel={linha_alvo.linha_excel}",
                    tipo_diferenca="LINHA_SEM_PAR",
                    nivel_correspondencia="SEM_PAR",
                    score_correspondencia=0,
                )
            )

        return pares, diferencas, len(sem_par_base), len(sem_par_alvo)

    def _comparar_par_linhas(
        self,
        obra_id: int,
        chave_ligacao: str,
        linha_base: LinhaObra,
        linha_alvo: LinhaObra,
        par: ParCorrespondencia,
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
                    tipo_diferenca=self._classificar_tipo_diferenca(campo, valor_base, valor_alvo),
                    nivel_correspondencia=par.nivel_correspondencia,
                    score_correspondencia=par.score_correspondencia,
                )
            )

        return diferencas

    @staticmethod
    def _classificar_tipo_diferenca(campo: str, valor_base: object, valor_alvo: object) -> str:
        """Classifica a diferenca de forma mais util para leitura humana."""
        if campo == "descricao":
            return "DESCRICAO_ALTERADA"

        if campo == "material":
            return "MATERIAL_ALTERADO"

        if campo == "artigo":
            return "ARTIGO_ALTERADO"

        if campo == "veio":
            return "VEIO_ALTERADO"

        if campo in {"comp", "larg", "qt", "esp", "esp_mat", "esp_final"}:
            return "MEDIDA_ALTERADA"

        if campo.startswith("orla_"):
            return "ORLA_ALTERADA"

        if campo.startswith("cnc_"):
            return "CNC_ALTERADO"

        if campo == "notas":
            valor_base_limpo = (str(valor_base).strip() if valor_base is not None else "")
            valor_alvo_limpo = (str(valor_alvo).strip() if valor_alvo is not None else "")

            if not valor_base_limpo and valor_alvo_limpo:
                return "NOTA_ADICIONADA"
            if valor_base_limpo and not valor_alvo_limpo:
                return "NOTA_REMOVIDA"
            return "NOTA_ALTERADA"

        return "CAMPO_ALTERADO"

    @staticmethod
    def top_tipos_diferenca(resumo: ResumoComparacaoEstados, limite: int = 10) -> list[tuple[str, int]]:
        """Devolve os tipos de diferenca mais frequentes."""
        contagem = Counter(diferenca.tipo_diferenca for diferenca in resumo.diferencas)
        return contagem.most_common(limite)

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

    @staticmethod
    def _agrupar_por_assinatura_forte(linhas: list[LinhaObra]) -> dict[str, list[LinhaObra]]:
        """Agrupa linhas por assinatura forte."""
        grupos: dict[str, list[LinhaObra]] = defaultdict(list)

        for linha in linhas:
            assinatura_forte = linha.gerar_assinatura_forte()
            if not assinatura_forte:
                continue
            grupos[assinatura_forte].append(linha)

        for assinatura_forte in grupos:
            grupos[assinatura_forte].sort(key=lambda linha: (linha.linha_excel, linha.id or 0))

        return dict(grupos)
