"""CO2 evitado e percentual de energia solar de cada sessao.

CO2 evitado = kWh vindo de energia solar x fator de emissao do SIN (Sistema
Interligado Nacional brasileiro) = 0.0817 kg/kWh.
"""

FATOR_EMISSAO_SIN_KG_POR_KWH = 0.0817


def calcular_energia_solar_kwh(kwh_consumido: float, percentual_solar: float) -> float:
    return round(kwh_consumido * (percentual_solar / 100), 3)


def calcular_co2_evitado_kg(kwh_solar: float) -> float:
    return round(kwh_solar * FATOR_EMISSAO_SIN_KG_POR_KWH, 3)
