from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UsuarioAdminOut(BaseModel):
    id: int
    nome: str
    email: EmailStr
    empresa: str | None
    telefone: str | None
    saldo: float
    qtd_veiculos: int
    qtd_sessoes_finalizadas: int
    criado_em: datetime


class UsuariosResumoOut(BaseModel):
    total_usuarios: int
    total_empresas: int
    usuarios: list[UsuarioAdminOut]


class PremiarUsuarioIn(BaseModel):
    valor: float = Field(gt=0, le=1000)
    motivo: str | None = None


class PremiarUsuarioOut(BaseModel):
    usuario_id: int
    saldo_atual: float
    mensagem: str
