from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FilaEntrar(BaseModel):
    veiculo_id: int


class FilaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    veiculo_id: int
    prioridade: str
    posicao_fila: int
    criado_em: datetime
    status: str


class FilaPosicaoOut(BaseModel):
    posicao_fila: int
    prioridade: str
    pessoas_a_frente: int
    previsao_espera_min: float
    status: str
