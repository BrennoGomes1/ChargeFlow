from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Sessao(Base):
    __tablename__ = "sessoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculos.id", ondelete="CASCADE"), nullable=False)
    estacao_id: Mapped[int] = mapped_column(ForeignKey("estacoes.id", ondelete="CASCADE"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)

    limite_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=80)
    limite_custo: Mapped[float | None] = mapped_column(Numeric(10, 2))

    inicio: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    fim: Mapped[datetime | None] = mapped_column(DateTime)

    kwh_consumido: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False, default=0)
    potencia_alocada_kw: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    custo_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    tarifa_aplicada: Mapped[float | None] = mapped_column(Numeric(6, 4))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="carregando")
    kwh_solar: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False, default=0)
    co2_evitado_kg: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False, default=0)

    veiculo = relationship("Veiculo", back_populates="sessoes")
    estacao = relationship("Estacao", back_populates="sessoes")
    usuario = relationship("Usuario", back_populates="sessoes")
