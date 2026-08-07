from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SaldoOut(BaseModel):
    saldo_atual: float


class RecarregarSaldoIn(BaseModel):
    valor: float = Field(gt=0, le=10000)


class EstimativaSaldoOut(BaseModel):
    veiculo_id: int
    saldo_atual: float
    tarifa_vigente: float
    horario_pico: bool
    bateria_atual_percent: float
    percentual_maximo_alcancavel: float
    kwh_maximo_alcancavel: float


class MovimentacaoSaldoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: str
    valor: float
    saldo_apos: float
    sessao_id: int | None
    descricao: str | None
    criado_em: datetime
