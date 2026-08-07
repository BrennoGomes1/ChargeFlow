from pydantic import BaseModel


class ConsumoPontoOut(BaseModel):
    periodo: str
    kwh_total: float
    custo_total: float
    sessoes: int


class ConsumoOut(BaseModel):
    pontos: list[ConsumoPontoOut]
    kwh_total: float
    custo_total: float


class SustentabilidadeOut(BaseModel):
    kwh_total: float
    kwh_solar_total: float
    percentual_renovavel: float
    co2_evitado_total_kg: float


class RankingItemOut(BaseModel):
    nome: str
    empresa: str | None
    kwh_total: float
    custo_total: float
    sessoes: int
