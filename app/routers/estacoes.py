from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.config import ConfigPredio
from app.models.estacao import Estacao
from app.models.sessao import Sessao
from app.schemas.estacao import EstacaoOut, EstacaoSessaoOut, PotenciaPredioOut
from app.security import exigir_admin, obter_usuario_atual
from app.services.priorizacao import calcular_prioridade
from app.services.tarifacao import calcular_custo_sessao, esta_em_horario_pico

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
    horario_pico = esta_em_horario_pico(
        datetime.now(), config.horario_pico_inicio, config.horario_pico_fim
    )

    return PotenciaPredioOut(
        potencia_max_total_kw=maximo,
        potencia_em_uso_kw=round(em_uso, 2),
        potencia_disponivel_kw=round(max(maximo - em_uso, 0), 2),
        percentual_em_uso=round((em_uso / maximo) * 100, 1) if maximo > 0 else 0,
        horario_pico=horario_pico,
    )


@router.get("/{estacao_id}/sessao", response_model=EstacaoSessaoOut)
def sessao_da_estacao(
    estacao_id: int, db: Session = Depends(get_db), _admin=Depends(exigir_admin)
):
    sessao = (
        db.query(Sessao)
        .options(joinedload(Sessao.veiculo), joinedload(Sessao.usuario), joinedload(Sessao.estacao))
        .filter(Sessao.estacao_id == estacao_id, Sessao.status == "carregando")
        .first()
    )
    if not sessao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma recarga em andamento nessa estacao"
        )

    config = _config(db)
    veiculo = sessao.veiculo
    agora = datetime.now()

    horas_decorridas = max((agora - sessao.inicio).total_seconds() / 3600, 0.0)
    bateria_inicial = float(veiculo.bateria_atual_percent)
    kwh_maximo_bateria = float(veiculo.capacidade_bateria_kwh) * max(100 - bateria_inicial, 0) / 100
    kwh_estimado = min(float(sessao.potencia_alocada_kw) * horas_decorridas, kwh_maximo_bateria)
    bateria_estimada = min(
        bateria_inicial + (kwh_estimado / float(veiculo.capacidade_bateria_kwh)) * 100, 100
    )
    custo_estimado, _ = calcular_custo_sessao(
        sessao.inicio,
        agora,
        kwh_estimado,
        float(config.tarifa_pico),
        float(config.tarifa_fora_pico),
        config.horario_pico_inicio,
        config.horario_pico_fim,
    )

    return EstacaoSessaoOut(
        estacao_id=sessao.estacao_id,
        estacao_nome=sessao.estacao.nome,
        usuario_nome=sessao.usuario.nome,
        usuario_empresa=sessao.usuario.empresa,
        veiculo_placa=veiculo.placa,
        veiculo_modelo=veiculo.modelo,
        veiculo_marca=veiculo.marca,
        bateria_atual_percent=round(bateria_estimada, 1),
        limite_percent=float(sessao.limite_percent),
        prioridade=calcular_prioridade(bateria_estimada),
        potencia_alocada_kw=float(sessao.potencia_alocada_kw),
        kwh_consumido=round(kwh_estimado, 3),
        custo_total=round(custo_estimado, 2),
        tempo_decorrido_min=round(horas_decorridas * 60, 1),
    )
