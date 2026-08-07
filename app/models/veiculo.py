from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Veiculo(Base):
    __tablename__ = "veiculos"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    placa: Mapped[str] = mapped_column(String(10), nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), nullable=False)
    marca: Mapped[str | None] = mapped_column(String(80))
    capacidade_bateria_kwh: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    bateria_atual_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    limite_percent_padrao: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=80)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    usuario = relationship("Usuario", back_populates="veiculos")
    sessoes = relationship("Sessao", back_populates="veiculo", cascade="all, delete-orphan")
    entradas_fila = relationship("FilaEspera", back_populates="veiculo", cascade="all, delete-orphan")
