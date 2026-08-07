from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UsuarioRegistrar(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    empresa: str | None = None
    telefone: str | None = None


class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    role: str
    empresa: str | None
    telefone: str | None
    saldo: float
    criado_em: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
