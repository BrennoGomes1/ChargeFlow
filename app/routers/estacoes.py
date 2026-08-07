from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.config import ConfigPredio
from app.models.estacao import Estacao
from app.schemas.estacao import EstacaoOut, PotenciaPredioOut
from app.security import obter_usuario_atual
from app.services.tarifacao import esta_em_horario_ponta

router = APIRouter(prefix="/api/estacoes", tags=["Estacoes"])


def _config(db: Session) -> ConfigPredio:
    config = db.query(ConfigPredio).first()
    if not config:
        raise HTTPException(status_code=500, detail="Configuracao do predio nao encontrada")
    return config


@router.get("", response_model=list[EstacaoOut])
def listar_estacoes(db: Session = Depends(get_db), _usuario=Depends(obter_usuario_atual)):
    return db.query(Estacao).order_by(Estacao.nome).all()


@router.get("/potencia", response_model=PotenciaPredioOut)
def potencia_predio(db: Session = Depends(get_db), _usuario=Depends(obter_usuario_atual)):
    config = _config(db)
    em_uso = db.query(func.coalesce(func.sum(Estacao.potencia_atual_kw), 0)).scalar()
    em_uso = float(em_uso)
    maximo = float(config.potencia_max_total_kw)
    horario_ponta = esta_em_horario_ponta(
        datetime.now(), config.horario_ponta_inicio, config.horario_ponta_fim
    )

    return PotenciaPredioOut(
        potencia_max_total_kw=maximo,
        potencia_em_uso_kw=round(em_uso, 2),
        potencia_disponivel_kw=round(max(maximo - em_uso, 0), 2),
        percentual_em_uso=round((em_uso / maximo) * 100, 1) if maximo > 0 else 0,
        horario_ponta=horario_ponta,
    )
