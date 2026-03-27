"""Serviço base para futura gestão de sugestões de notas."""

from __future__ import annotations

from pathlib import Path

from models.schemas import SugestaoNotaLog
from utils.helpers import escrever_json_linha, timestamp_atual


class ServicoSugestoes:
    """Centraliza a criação e o registo de eventos ligados a sugestões.

    Nesta fase, o serviço ainda não decide notas de forma inteligente.
    Ele existe para preparar o ponto onde essa lógica será colocada.
    """

    # TODO: adicionar regras simples quando existirem exemplos reais validados.
    REGRAS_INICIAIS_TOKENS: dict[str, str] = {}

    def __init__(self, pasta_logs: Path) -> None:
        """Define o local onde os registos locais serão guardados."""
        self.pasta_logs = Path(pasta_logs)
        self.caminho_log = self.pasta_logs / "sugestoes_notas.log"

    def criar_registo(
        self,
        linha_obra_id: int | None,
        nota_original: str,
        tokens_encontrados: list[str],
        origem_sugestao: str = "placeholder",
    ) -> SugestaoNotaLog:
        """Cria um objeto de log com informação mínima para análise futura."""
        sugestao_texto = self._procurar_sugestao_por_tokens(tokens_encontrados)

        return SugestaoNotaLog(
            linha_obra_id=linha_obra_id,
            sugestao_texto=sugestao_texto,
            nota_original=nota_original,
            origem_sugestao=origem_sugestao,
            confianca=None,
            estado="pendente",
            detalhes_json={"tokens_encontrados": tokens_encontrados},
            criado_em=timestamp_atual(),
        )

    def registar_localmente(self, registo: SugestaoNotaLog) -> None:
        """Guarda o registo em formato JSON linha a linha dentro da pasta de logs."""
        escrever_json_linha(self.caminho_log, registo.para_dict())

    def _procurar_sugestao_por_tokens(self, tokens_encontrados: list[str]) -> str | None:
        """Procura uma sugestão simples baseada em regras manuais.

        O comportamento atual é conservador:
        devolve apenas o que estiver explicitamente definido no mapa de regras.
        """
        for token in tokens_encontrados:
            if token in self.REGRAS_INICIAIS_TOKENS:
                return self.REGRAS_INICIAIS_TOKENS[token]

        return None
