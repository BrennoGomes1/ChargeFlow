from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="usuario")
    empresa: Mapped[str | None] = mapped_column(String(120))
    telefone: Mapped[str | None] = mapped_column(String(30))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    veiculos = relationship("Veiculo", back_populates="usuario", cascade="all, delete-orphan")
    sessoes = relationship("Sessao", back_populates="usuario", cascade="all, delete-orphan")
    entradas_fila = relationship("FilaEspera", back_populates="usuario", cascade="all, delete-orphan")
