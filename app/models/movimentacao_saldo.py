from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MovimentacaoSaldo(Base):
    __tablename__ = "movimentacoes_saldo"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)  # 'recarga' ou 'consumo'
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    saldo_apos: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sessao_id: Mapped[int | None] = mapped_column(ForeignKey("sessoes.id", ondelete="SET NULL"))
    descricao: Mapped[str | None] = mapped_column(String(200))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    usuario = relationship("Usuario", back_populates="movimentacoes_saldo")
