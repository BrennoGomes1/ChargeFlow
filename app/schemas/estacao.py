from pydantic import BaseModel, ConfigDict


class EstacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    potencia_max_kw: float
    potencia_atual_kw: float
    status: str
    localizacao: str | None


class PotenciaPredioOut(BaseModel):
    potencia_max_total_kw: float
    potencia_em_uso_kw: float
    potencia_disponivel_kw: float
    percentual_em_uso: float
    horario_ponta: bool
