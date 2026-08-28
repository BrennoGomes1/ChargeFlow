from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.estacao import Estacao
from app.models.sessao import Sessao
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.schemas.dashboard import (
    ConsumoOut,
    ConsumoPontoOut,
    HistoricoItemOut,
    RankingItemOut,
    SustentabilidadeOut,
)
from app.security import exigir_admin

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard (Admin)"])

_TRUNC = {"dia": "day", "semana": "week", "mes": "month"}


@router.get("/consumo", response_model=ConsumoOut)
def consumo(
    periodo: str = Query("dia", pattern="^(dia|semana|mes)$"),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_admin),
):
    bucket = func.date_trunc(_TRUNC[periodo], Sessao.inicio)
    linhas = (
        db.query(
            bucket.label("periodo"),
            func.coalesce(func.sum(Sessao.kwh_consumido), 0).label("kwh"),
            func.coalesce(func.sum(Sessao.custo_total), 0).label("custo"),
            func.count(Sessao.id).label("sessoes"),
        )
        .filter(Sessao.status == "finalizada")
        .group_by(bucket)
        .order_by(bucket)
        .all()
    )

    pontos = [
        ConsumoPontoOut(
            periodo=linha.periodo.strftime("%Y-%m-%d"),
            kwh_total=float(linha.kwh),
            custo_total=float(linha.custo),
            sessoes=linha.sessoes,
        )
        for linha in linhas
    ]

    return ConsumoOut(
        pontos=pontos,
        kwh_total=round(sum(p.kwh_total for p in pontos), 2),
        custo_total=round(sum(p.custo_total for p in pontos), 2),
    )


@router.get("/sustentabilidade", response_model=SustentabilidadeOut)
def sustentabilidade(db: Session = Depends(get_db), _admin: Usuario = Depends(exigir_admin)):
    kwh_total, kwh_solar_total, co2_total = (
        db.query(
            func.coalesce(func.sum(Sessao.kwh_consumido), 0),
            func.coalesce(func.sum(Sessao.kwh_solar), 0),
            func.coalesce(func.sum(Sessao.co2_evitado_kg), 0),
        )
        .filter(Sessao.status == "finalizada")
        .first()
    )
    kwh_total, kwh_solar_total, co2_total = float(kwh_total), float(kwh_solar_total), float(co2_total)
    percentual_renovavel = round((kwh_solar_total / kwh_total) * 100, 1) if kwh_total > 0 else 0.0

    return SustentabilidadeOut(
        kwh_total=round(kwh_total, 2),
        kwh_solar_total=round(kwh_solar_total, 2),
        percentual_renovavel=percentual_renovavel,
        co2_evitado_total_kg=round(co2_total, 3),
    )


@router.get("/ranking", response_model=list[RankingItemOut])
def ranking(db: Session = Depends(get_db), _admin: Usuario = Depends(exigir_admin)):
    linhas = (
        db.query(
            Usuario.id,
            Usuario.nome,
            Usuario.empresa,
            func.coalesce(func.sum(Sessao.kwh_consumido), 0).label("kwh"),
            func.coalesce(func.sum(Sessao.custo_total), 0).label("custo"),
            func.count(Sessao.id).label("sessoes"),
        )
        .join(Sessao, Sessao.usuario_id == Usuario.id)
        .filter(Sessao.status == "finalizada")
        .group_by(Usuario.id, Usuario.nome, Usuario.empresa)
        .order_by(func.sum(Sessao.kwh_consumido).desc())
        .all()
    )

    return [
        RankingItemOut(
            usuario_id=linha.id,
            nome=linha.nome,
            empresa=linha.empresa,
            kwh_total=float(linha.kwh),
            custo_total=float(linha.custo),
            sessoes=linha.sessoes,
        )
        for linha in linhas
    ]


@router.get("/historico", response_model=list[HistoricoItemOut])
def historico_admin(
    limite: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_admin),
):
    linhas = (
        db.query(Sessao, Usuario, Veiculo, Estacao)
        .join(Usuario, Sessao.usuario_id == Usuario.id)
        .join(Veiculo, Sessao.veiculo_id == Veiculo.id)
        .join(Estacao, Sessao.estacao_id == Estacao.id)
        .filter(Sessao.status == "finalizada")
        .order_by(Sessao.fim.desc())
        .limit(limite)
        .all()
    )

    return [
        HistoricoItemOut(
            id=sessao.id,
            inicio=sessao.inicio,
            fim=sessao.fim,
            usuario_nome=usuario.nome,
            usuario_empresa=usuario.empresa,
            veiculo_placa=veiculo.placa,
            veiculo_modelo=veiculo.modelo,
            estacao_nome=estacao.nome,
            kwh_consumido=float(sessao.kwh_consumido),
            custo_total=float(sessao.custo_total),
            tarifa_aplicada=float(sessao.tarifa_aplicada) if sessao.tarifa_aplicada is not None else None,
            kwh_solar=float(sessao.kwh_solar),
            co2_evitado_kg=float(sessao.co2_evitado_kg),
        )
        for sessao, usuario, veiculo, estacao in linhas
    ]
