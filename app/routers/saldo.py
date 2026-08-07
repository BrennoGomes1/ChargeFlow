from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.config import ConfigPredio
from app.models.movimentacao_saldo import MovimentacaoSaldo
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.schemas.saldo import (
    EstimativaSaldoOut,
    MovimentacaoSaldoOut,
    RecarregarSaldoIn,
    SaldoOut,
)
from app.security import obter_usuario_atual
from app.services.saldo import estimar_percentual_alcancavel
from app.services.tarifacao import esta_em_horario_pico, tarifa_vigente

router = APIRouter(prefix="/api/saldo", tags=["Saldo"])


def _config(db: Session) -> ConfigPredio:
    config = db.query(ConfigPredio).first()
    if not config:
        raise HTTPException(status_code=500, detail="Configuracao do predio nao encontrada")
    return config


@router.get("", response_model=SaldoOut)
def ver_saldo(usuario: Usuario = Depends(obter_usuario_atual)):
    return SaldoOut(saldo_atual=float(usuario.saldo))


@router.post("/recarregar", response_model=SaldoOut)
def recarregar_saldo(
    dados: RecarregarSaldoIn,
    usuario: Usuario = Depends(obter_usuario_atual),
    db: Session = Depends(get_db),
):
    usuario.saldo = float(usuario.saldo) + dados.valor
    db.add(
        MovimentacaoSaldo(
            usuario_id=usuario.id,
            tipo="recarga",
            valor=dados.valor,
            saldo_apos=usuario.saldo,
            descricao="Recarga de saldo",
        )
    )
    db.commit()
    db.refresh(usuario)
    return SaldoOut(saldo_atual=float(usuario.saldo))


@router.get("/estimativa/{veiculo_id}", response_model=EstimativaSaldoOut)
def estimativa_saldo(
    veiculo_id: int,
    usuario: Usuario = Depends(obter_usuario_atual),
    db: Session = Depends(get_db),
):
    veiculo = db.get(Veiculo, veiculo_id)
    if not veiculo or veiculo.usuario_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veiculo nao encontrado")

    config = _config(db)
    agora = datetime.now()
    horario_pico = esta_em_horario_pico(agora, config.horario_pico_inicio, config.horario_pico_fim)
    tarifa_atual = tarifa_vigente(
        agora, float(config.tarifa_pico), float(config.tarifa_fora_pico),
        config.horario_pico_inicio, config.horario_pico_fim,
    )

    percentual_max, kwh_max = estimar_percentual_alcancavel(
        float(usuario.saldo), tarifa_atual, float(veiculo.bateria_atual_percent), float(veiculo.capacidade_bateria_kwh)
    )

    return EstimativaSaldoOut(
        veiculo_id=veiculo.id,
        saldo_atual=float(usuario.saldo),
        tarifa_vigente=tarifa_atual,
        horario_pico=horario_pico,
        bateria_atual_percent=float(veiculo.bateria_atual_percent),
        percentual_maximo_alcancavel=percentual_max,
        kwh_maximo_alcancavel=kwh_max,
    )


@router.get("/extrato", response_model=list[MovimentacaoSaldoOut])
def extrato_saldo(usuario: Usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    return (
        db.query(MovimentacaoSaldo)
        .filter(MovimentacaoSaldo.usuario_id == usuario.id)
        .order_by(MovimentacaoSaldo.criado_em.desc())
        .all()
    )
