from datetime import datetime

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
    usuario_id: int
    nome: str
    empresa: str | None
    kwh_total: float
    custo_total: float
    sessoes: int


class HistoricoItemOut(BaseModel):
    id: int
    inicio: datetime
    fim: datetime | None
    usuario_nome: str
    usuario_empresa: str | None
    veiculo_placa: str
    veiculo_modelo: str
    estacao_nome: str
    kwh_consumido: float
    custo_total: float
    tarifa_aplicada: float | None
    kwh_solar: float
    co2_evitado_kg: float
