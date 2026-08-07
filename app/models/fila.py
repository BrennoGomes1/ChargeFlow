from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FilaEspera(Base):
    __tablename__ = "fila_espera"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculos.id", ondelete="CASCADE"), nullable=False)
    prioridade: Mapped[str] = mapped_column(String(10), nullable=False)
    posicao_fila: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="aguardando")

    usuario = relationship("Usuario", back_populates="entradas_fila")
    veiculo = relationship("Veiculo", back_populates="entradas_fila")
