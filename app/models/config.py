from datetime import time

from sqlalchemy import Numeric, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConfigPredio(Base):
    __tablename__ = "config_predio"

    id: Mapped[int] = mapped_column(primary_key=True)
    potencia_max_total_kw: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    tarifa_ponta: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    tarifa_fora_ponta: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    horario_ponta_inicio: Mapped[time] = mapped_column(Time, nullable=False, default=time(17, 0))
    horario_ponta_fim: Mapped[time] = mapped_column(Time, nullable=False, default=time(22, 0))
    percentual_solar: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=30)
