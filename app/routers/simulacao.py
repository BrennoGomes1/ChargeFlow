from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.config import ConfigPredio
from app.models.estacao import Estacao
from app.schemas.simulacao import (
    CarroSimuladoResultado,
    EstadoTempoRealOut,
    SimulacaoRequest,
    SimulacaoResultado,
)
from app.security import obter_usuario_atual
from app.services.potencia import (
    REDUCAO_HORARIO_PICO,
    CandidatoPotencia,
    alocar_potencia,
    potencia_efetiva_predio,
)
from app.services.priorizacao import calcular_prioridade
from app.services.tarifacao import esta_em_horario_pico

router = APIRouter(prefix="/api/simulacao", tags=["Simulacao"])


def _config(db: Session) -> ConfigPredio:
    config = db.query(ConfigPredio).first()
    if not config:
        raise HTTPException(status_code=500, detail="Configuracao do predio nao encontrada")
    return config


@router.post("/cenario", response_model=SimulacaoResultado)
def simular_cenario(
    dados: SimulacaoRequest, db: Session = Depends(get_db), _usuario=Depends(obter_usuario_atual)
):
    config = _config(db)
    agora = datetime.now()
    horario_pico = esta_em_horario_pico(agora, config.horario_pico_inicio, config.horario_pico_fim)

    em_uso_real = float(
        db.query(func.coalesce(func.sum(Estacao.potencia_atual_kw), 0)).scalar()
    )
    potencia_efetiva = potencia_efetiva_predio(float(config.potencia_max_total_kw), horario_pico)
    disponivel_para_simulacao = max(potencia_efetiva - em_uso_real, 0.0)

    candidatos = [
        CandidatoPotencia(
            chave=index,
            potencia_solicitada_kw=carro.potencia_max_kw,
            bateria_atual_percent=carro.bateria_atual_percent,
        )
        for index, carro in enumerate(dados.carros)
    ]
    alocado = alocar_potencia(candidatos, disponivel_para_simulacao)

    resultado_carros = [
        CarroSimuladoResultado(
            nome=carro.nome,
            bateria_atual_percent=carro.bateria_atual_percent,
            potencia_solicitada_kw=carro.potencia_max_kw,
            prioridade=calcular_prioridade(carro.bateria_atual_percent),
            potencia_alocada_kw=alocado.get(index, 0.0),
        )
        for index, carro in enumerate(dados.carros)
    ]

    return SimulacaoResultado(
        potencia_max_predio_kw=float(config.potencia_max_total_kw),
        potencia_ja_em_uso_kw=round(em_uso_real, 2),
        potencia_disponivel_kw=round(disponivel_para_simulacao, 2),
        horario_pico=horario_pico,
        reducao_horario_pico_percent=REDUCAO_HORARIO_PICO * 100 if horario_pico else 0,
        carros=resultado_carros,
        potencia_total_alocada_kw=round(sum(alocado.values()), 2),
    )


@router.get("/potencia-tempo-real", response_model=EstadoTempoRealOut)
def potencia_tempo_real(db: Session = Depends(get_db), _usuario=Depends(obter_usuario_atual)):
    config = _config(db)
    agora = datetime.now()
    horario_pico = esta_em_horario_pico(agora, config.horario_pico_inicio, config.horario_pico_fim)

    estacoes = db.query(Estacao).order_by(Estacao.nome).all()
    em_uso = sum(float(e.potencia_atual_kw) for e in estacoes)
    maximo = float(config.potencia_max_total_kw)

    return EstadoTempoRealOut(
        potencia_max_total_kw=maximo,
        potencia_em_uso_kw=round(em_uso, 2),
        potencia_disponivel_kw=round(max(maximo - em_uso, 0), 2),
        horario_pico=horario_pico,
        estacoes=[
            {
                "id": e.id,
                "nome": e.nome,
                "status": e.status,
                "potencia_max_kw": float(e.potencia_max_kw),
                "potencia_atual_kw": float(e.potencia_atual_kw),
                "localizacao": e.localizacao,
            }
            for e in estacoes
        ],
    )
