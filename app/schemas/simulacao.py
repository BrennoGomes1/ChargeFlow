from pydantic import BaseModel, Field


class CarroSimulado(BaseModel):
    nome: str = "Carro"
    bateria_atual_percent: float = Field(ge=0, le=100)
    potencia_max_kw: float = Field(gt=0)


class SimulacaoRequest(BaseModel):
    carros: list[CarroSimulado]


class CarroSimuladoResultado(BaseModel):
    nome: str
    bateria_atual_percent: float
    potencia_solicitada_kw: float
    prioridade: str
    potencia_alocada_kw: float


class SimulacaoResultado(BaseModel):
    potencia_max_predio_kw: float
    potencia_ja_em_uso_kw: float
    potencia_disponivel_kw: float
    horario_ponta: bool
    reducao_horario_ponta_percent: float
    carros: list[CarroSimuladoResultado]
    potencia_total_alocada_kw: float


class EstadoTempoRealOut(BaseModel):
    potencia_max_total_kw: float
    potencia_em_uso_kw: float
    potencia_disponivel_kw: float
    horario_ponta: bool
    estacoes: list[dict]
