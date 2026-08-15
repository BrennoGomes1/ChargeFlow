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
    horario_pico: bool


class EstacaoSessaoOut(BaseModel):
    estacao_id: int
    estacao_nome: str
    usuario_nome: str
    usuario_empresa: str | None
    veiculo_placa: str
    veiculo_modelo: str
    veiculo_marca: str | None
    bateria_atual_percent: float
    limite_percent: float
    prioridade: str
    potencia_alocada_kw: float
    kwh_consumido: float
    custo_total: float
    tempo_decorrido_min: float
