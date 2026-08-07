from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VeiculoCreate(BaseModel):
    placa: str
    modelo: str
    marca: str | None = None
    capacidade_bateria_kwh: float = Field(gt=0)
    bateria_atual_percent: float = Field(default=0, ge=0, le=100)
    limite_percent_padrao: float = Field(default=80, ge=1, le=100)


class VeiculoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    placa: str
    modelo: str
    marca: str | None
    capacidade_bateria_kwh: float
    bateria_atual_percent: float
    limite_percent_padrao: float
    criado_em: datetime
