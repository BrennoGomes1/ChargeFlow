from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Estacao(Base):
    __tablename__ = "estacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    potencia_max_kw: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    potencia_atual_kw: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="disponivel")
    localizacao: Mapped[str | None] = mapped_column(String(120))

    sessoes = relationship("Sessao", back_populates="estacao")
