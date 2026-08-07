"""Calculo de tarifa e custo das sessoes de recarga.

Horario de pico: tarifa mais cara. Fora de pico: tarifa mais barata. Quando
uma sessao cruza os dois horarios, o consumo e dividido proporcionalmente ao
tempo passado em cada faixa.
"""

from datetime import datetime, time, timedelta


def esta_em_horario_pico(momento: datetime, inicio_pico: time, fim_pico: time) -> bool:
    hora = momento.time()
    if inicio_pico <= fim_pico:
        return inicio_pico <= hora < fim_pico
    return hora >= inicio_pico or hora < fim_pico  # faixa cruza a meia-noite


def tarifa_vigente(
    momento: datetime,
    tarifa_pico: float,
    tarifa_fora_pico: float,
    inicio_pico: time,
    fim_pico: time,
) -> float:
    if esta_em_horario_pico(momento, inicio_pico, fim_pico):
        return tarifa_pico
    return tarifa_fora_pico


def _dividir_kwh_pico_fora_pico(
    inicio: datetime, fim: datetime, kwh_total: float, inicio_pico: time, fim_pico: time
) -> tuple[float, float]:
    duracao_total = (fim - inicio).total_seconds()
    if duracao_total <= 0 or kwh_total <= 0:
        return 0.0, 0.0

    passos = min(max(int(duracao_total // 60), 1), 1440)
    intervalo = duracao_total / passos
    minutos_pico = 0
    for i in range(passos):
        momento = inicio + timedelta(seconds=intervalo * (i + 0.5))
        if esta_em_horario_pico(momento, inicio_pico, fim_pico):
            minutos_pico += 1

    proporcao_pico = minutos_pico / passos
    kwh_pico = kwh_total * proporcao_pico
    return kwh_pico, kwh_total - kwh_pico


def calcular_custo_sessao(
    inicio: datetime,
    fim: datetime,
    kwh_total: float,
    tarifa_pico: float,
    tarifa_fora_pico: float,
    inicio_pico: time,
    fim_pico: time,
) -> tuple[float, float]:
    """Retorna (custo_total, tarifa_media_aplicada)."""
    kwh_pico, kwh_fora_pico = _dividir_kwh_pico_fora_pico(
        inicio, fim, kwh_total, inicio_pico, fim_pico
    )
    custo = kwh_pico * tarifa_pico + kwh_fora_pico * tarifa_fora_pico
    tarifa_media = (custo / kwh_total) if kwh_total > 0 else tarifa_fora_pico
    return round(custo, 2), round(tarifa_media, 4)
