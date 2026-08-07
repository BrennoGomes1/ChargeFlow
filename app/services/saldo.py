"""Estimativa de quanto de bateria um usuario consegue carregar com o saldo
que tem disponivel, dada a tarifa vigente no momento.
"""


def estimar_percentual_alcancavel(
    saldo_atual: float,
    tarifa_vigente: float,
    bateria_atual_percent: float,
    capacidade_bateria_kwh: float,
) -> tuple[float, float]:
    """Retorna (percentual_maximo_alcancavel, kwh_maximo_alcancavel)."""
    if tarifa_vigente <= 0 or capacidade_bateria_kwh <= 0:
        return bateria_atual_percent, 0.0

    kwh_alcancavel = saldo_atual / tarifa_vigente
    percentual_alcancavel = bateria_atual_percent + (kwh_alcancavel / capacidade_bateria_kwh) * 100
    percentual_alcancavel = min(percentual_alcancavel, 100.0)

    kwh_ate_o_maximo = capacidade_bateria_kwh * (percentual_alcancavel - bateria_atual_percent) / 100
    return round(percentual_alcancavel, 1), round(max(kwh_ate_o_maximo, 0.0), 3)
