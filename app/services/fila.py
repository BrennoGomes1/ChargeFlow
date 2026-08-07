"""Gerenciamento da fila de espera quando todas as estacoes estao ocupadas.

A fila e ordenada por prioridade (bateria mais baixa primeiro) e, dentro da
mesma prioridade, por ordem de chegada.
"""

from app.services.priorizacao import ORDEM_PRIORIDADE, calcular_prioridade

TEMPO_MEDIO_SESSAO_MIN = 45.0


def prioridade_para_fila(bateria_atual_percent: float) -> str:
    return calcular_prioridade(bateria_atual_percent)


def calcular_posicao(fila_atual: list, nova_prioridade: str) -> int:
    """Posicao (1-indexada) de um novo item, inserido apos os de prioridade igual ou maior."""
    posicao = 1
    for item in fila_atual:
        if ORDEM_PRIORIDADE[item.prioridade] <= ORDEM_PRIORIDADE[nova_prioridade]:
            posicao += 1
    return posicao


def reordenar(fila_atual: list) -> list:
    return sorted(fila_atual, key=lambda item: (ORDEM_PRIORIDADE[item.prioridade], item.criado_em))


def estimar_espera_minutos(posicao_fila: int) -> float:
    pessoas_a_frente = max(posicao_fila - 1, 0)
    return round(pessoas_a_frente * TEMPO_MEDIO_SESSAO_MIN, 1)
