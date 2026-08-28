from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessaoIniciar(BaseModel):
    veiculo_id: int
    estacao_id: int
    limite_percent: float | None = Field(default=None, ge=1, le=100)
    limite_custo: float | None = Field(default=None, ge=0)


class SessaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    veiculo_id: int
    estacao_id: int
    usuario_id: int
    limite_percent: float
    limite_custo: float | None
    inicio: datetime
    fim: datetime | None
    kwh_consumido: float
    potencia_alocada_kw: float
    custo_total: float
    tarifa_aplicada: float | None
    status: str
    kwh_solar: float
    co2_evitado_kg: float


class SessaoStatusOut(BaseModel):
    id: int
    status: str
    bateria_atual_percent: float
    limite_percent: float
    kwh_consumido: float
    potencia_alocada_kw: float
    custo_total: float
    limite_custo: float | None
    tempo_decorrido_min: float
    tempo_estimado_restante_min: float | None
    kwh_solar: float | None = None
    co2_evitado_kg: float | None = None


class SessaoFinalizadaOut(BaseModel):
    id: int
    status: str
    kwh_consumido: float
    custo_total: float
    kwh_solar: float
    co2_evitado_kg: float
    mensagem: str
