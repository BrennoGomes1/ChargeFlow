"""Regras de priorizacao de recarga com base na bateria atual do veiculo.

Bateria < 30%  -> ALTA  (recebe mais potencia)
Bateria 30-70% -> MEDIA
Bateria > 70%  -> BAIXA (potencia reduzida, libera capacidade pros outros)
"""

PRIORIDADE_ALTA = "ALTA"
PRIORIDADE_MEDIA = "MEDIA"
PRIORIDADE_BAIXA = "BAIXA"

# Peso usado na distribuicao proporcional de potencia (quanto maior, mais potencia recebe)
PESO_PRIORIDADE = {
    PRIORIDADE_ALTA: 3.0,
    PRIORIDADE_MEDIA: 2.0,
    PRIORIDADE_BAIXA: 1.0,
}

ORDEM_PRIORIDADE = {
    PRIORIDADE_ALTA: 0,
    PRIORIDADE_MEDIA: 1,
    PRIORIDADE_BAIXA: 2,
}


def calcular_prioridade(bateria_atual_percent: float) -> str:
    if bateria_atual_percent < 30:
        return PRIORIDADE_ALTA
    if bateria_atual_percent <= 70:
        return PRIORIDADE_MEDIA
    return PRIORIDADE_BAIXA


def peso_prioridade(prioridade: str) -> float:
    return PESO_PRIORIDADE[prioridade]
