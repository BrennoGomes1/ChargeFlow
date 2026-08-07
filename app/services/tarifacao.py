"""Calculo de tarifa e custo das sessoes de recarga.

Horario de ponta: tarifa mais cara. Fora de ponta: tarifa mais barata. Quando
uma sessao cruza os dois horarios, o consumo e dividido proporcionalmente ao
tempo passado em cada faixa.
"""

from datetime import datetime, time, timedelta


def esta_em_horario_ponta(momento: datetime, inicio_ponta: time, fim_ponta: time) -> bool:
    hora = momento.time()
    if inicio_ponta <= fim_ponta:
        return inicio_ponta <= hora < fim_ponta
    return hora >= inicio_ponta or hora < fim_ponta  # faixa cruza a meia-noite


def tarifa_vigente(
    momento: datetime,
    tarifa_ponta: float,
    tarifa_fora_ponta: float,
    inicio_ponta: time,
    fim_ponta: time,
) -> float:
    if esta_em_horario_ponta(momento, inicio_ponta, fim_ponta):
        return tarifa_ponta
    return tarifa_fora_ponta


def _dividir_kwh_ponta_fora_ponta(
    inicio: datetime, fim: datetime, kwh_total: float, inicio_ponta: time, fim_ponta: time
) -> tuple[float, float]:
    duracao_total = (fim - inicio).total_seconds()
    if duracao_total <= 0 or kwh_total <= 0:
        return 0.0, 0.0

    passos = min(max(int(duracao_total // 60), 1), 1440)
    intervalo = duracao_total / passos
    minutos_ponta = 0
    for i in range(passos):
        momento = inicio + timedelta(seconds=intervalo * (i + 0.5))
        if esta_em_horario_ponta(momento, inicio_ponta, fim_ponta):
            minutos_ponta += 1

    proporcao_ponta = minutos_ponta / passos
    kwh_ponta = kwh_total * proporcao_ponta
    return kwh_ponta, kwh_total - kwh_ponta


def calcular_custo_sessao(
    inicio: datetime,
    fim: datetime,
    kwh_total: float,
    tarifa_ponta: float,
    tarifa_fora_ponta: float,
    inicio_ponta: time,
    fim_ponta: time,
) -> tuple[float, float]:
    """Retorna (custo_total, tarifa_media_aplicada)."""
    kwh_ponta, kwh_fora_ponta = _dividir_kwh_ponta_fora_ponta(
        inicio, fim, kwh_total, inicio_ponta, fim_ponta
    )
    custo = kwh_ponta * tarifa_ponta + kwh_fora_ponta * tarifa_fora_ponta
    tarifa_media = (custo / kwh_total) if kwh_total > 0 else tarifa_fora_ponta
    return round(custo, 2), round(tarifa_media, 4)
