"""Algoritmo de distribuicao inteligente de potencia entre estacoes ativas.

Estrategia: water-filling ponderado por prioridade. A potencia disponivel do
predio e distribuida entre os carros ativos proporcionalmente ao peso da sua
prioridade (bateria baixa pesa mais), respeitando o teto individual de cada
estacao. Quem satura o proprio teto sai da rodada e o restante da potencia e
redistribuido entre os demais, ate esgotar a potencia disponivel ou atender
todo mundo.
"""

from dataclasses import dataclass

from app.services.priorizacao import calcular_prioridade, peso_prioridade

REDUCAO_HORARIO_PICO = 0.20  # reduz 20% da potencia total do predio em horario de pico


@dataclass
class CandidatoPotencia:
    chave: object
    potencia_solicitada_kw: float
    bateria_atual_percent: float


def potencia_efetiva_predio(potencia_max_total_kw: float, horario_pico: bool) -> float:
    if horario_pico:
        return round(potencia_max_total_kw * (1 - REDUCAO_HORARIO_PICO), 2)
    return round(potencia_max_total_kw, 2)


def alocar_potencia(
    candidatos: list[CandidatoPotencia], potencia_disponivel_kw: float
) -> dict[object, float]:
    pendentes = {
        c.chave: {
            "solicitada": max(c.potencia_solicitada_kw, 0.0),
            "peso": peso_prioridade(calcular_prioridade(c.bateria_atual_percent)),
        }
        for c in candidatos
    }
    alocado = {c.chave: 0.0 for c in candidatos}
    disponivel = max(potencia_disponivel_kw, 0.0)

    while pendentes and disponivel > 1e-6:
        soma_pesos = sum(item["peso"] for item in pendentes.values())
        if soma_pesos <= 0:
            break

        propostas = {
            chave: disponivel * item["peso"] / soma_pesos for chave, item in pendentes.items()
        }

        saturados = {
            chave: pendentes[chave]["solicitada"]
            for chave, proposta in propostas.items()
            if proposta >= pendentes[chave]["solicitada"]
        }

        if not saturados:
            for chave, proposta in propostas.items():
                alocado[chave] += proposta
            disponivel = 0.0
            break

        for chave, valor in saturados.items():
            alocado[chave] += valor
            disponivel -= valor
            del pendentes[chave]

    return {chave: round(valor, 2) for chave, valor in alocado.items()}
