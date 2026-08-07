from pydantic import BaseModel


class EntradaOut(BaseModel):
    liberado: bool
    mensagem: str
    estacao_sugerida: str | None = None


class SaidaOut(BaseModel):
    liberado: bool
    mensagem: str
