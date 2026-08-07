from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.config import ConfigPredio
from app.models.estacao import Estacao
from app.models.sessao import Sessao
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.schemas.sessao import SessaoFinalizadaOut, SessaoIniciar, SessaoOut, SessaoStatusOut
from app.security import obter_usuario_atual
from app.services import fila as fila_service
from app.services.potencia import CandidatoPotencia, alocar_potencia, potencia_efetiva_predio
from app.services.sustentabilidade import calcular_co2_evitado_kg, calcular_energia_solar_kwh
from app.services.tarifacao import calcular_custo_sessao, esta_em_horario_ponta, tarifa_vigente

router = APIRouter(prefix="/api/sessoes", tags=["Sessoes de carregamento"])


def _config(db: Session) -> ConfigPredio:
    config = db.query(ConfigPredio).first()
    if not config:
        raise HTTPException(status_code=500, detail="Configuracao do predio nao encontrada")
    return config


def _recalcular_potencia_ativas(db: Session, config: ConfigPredio) -> None:
    """Redistribui a potencia do predio entre todas as sessoes 'carregando'."""
    ativas: list[Sessao] = (
        db.query(Sessao)
        .options(joinedload(Sessao.veiculo), joinedload(Sessao.estacao))
        .filter(Sessao.status == "carregando")
        .all()
    )
    if not ativas:
        return

    horario_ponta = esta_em_horario_ponta(
        datetime.now(), config.horario_ponta_inicio, config.horario_ponta_fim
    )
    potencia_disponivel = potencia_efetiva_predio(float(config.potencia_max_total_kw), horario_ponta)

    candidatos = [
        CandidatoPotencia(
            chave=sessao.id,
            potencia_solicitada_kw=float(sessao.estacao.potencia_max_kw),
            bateria_atual_percent=float(sessao.veiculo.bateria_atual_percent),
        )
        for sessao in ativas
    ]
    alocado = alocar_potencia(candidatos, potencia_disponivel)

    for sessao in ativas:
        potencia = alocado.get(sessao.id, 0.0)
        sessao.potencia_alocada_kw = potencia
        sessao.estacao.potencia_atual_kw = potencia
    db.flush()


def _reavaliar_fila(db: Session) -> None:
    from app.models.fila import FilaEspera

    vagas_livres = db.query(Estacao).filter(Estacao.status == "disponivel").count()
    if vagas_livres <= 0:
        return

    aguardando = (
        db.query(FilaEspera).filter(FilaEspera.status == "aguardando").all()
    )
    ordenada = fila_service.reordenar(aguardando)
    for item in ordenada[:vagas_livres]:
        item.status = "notificada"
    db.flush()


def _finalizar_sessao(db: Session, sessao: Sessao, config: ConfigPredio, agora: datetime) -> Sessao:
    veiculo = sessao.veiculo
    estacao = sessao.estacao

    horas_decorridas = max((agora - sessao.inicio).total_seconds() / 3600, 0.0)
    kwh_consumido = float(sessao.potencia_alocada_kw) * horas_decorridas

    kwh_maximo_bateria = float(veiculo.capacidade_bateria_kwh) * max(
        100 - float(veiculo.bateria_atual_percent), 0
    ) / 100
    kwh_consumido = min(kwh_consumido, kwh_maximo_bateria)

    custo_total, tarifa_media = calcular_custo_sessao(
        sessao.inicio,
        agora,
        kwh_consumido,
        float(config.tarifa_ponta),
        float(config.tarifa_fora_ponta),
        config.horario_ponta_inicio,
        config.horario_ponta_fim,
    )

    if sessao.limite_custo and custo_total > float(sessao.limite_custo) > 0:
        fator = float(sessao.limite_custo) / custo_total
        kwh_consumido = round(kwh_consumido * fator, 3)
        custo_total = float(sessao.limite_custo)

    kwh_solar = calcular_energia_solar_kwh(kwh_consumido, float(config.percentual_solar))
    co2_evitado = calcular_co2_evitado_kg(kwh_solar)

    sessao.fim = agora
    sessao.kwh_consumido = round(kwh_consumido, 3)
    sessao.custo_total = round(custo_total, 2)
    sessao.tarifa_aplicada = tarifa_media
    sessao.kwh_solar = kwh_solar
    sessao.co2_evitado_kg = co2_evitado
    sessao.status = "finalizada"

    veiculo.bateria_atual_percent = min(
        float(veiculo.bateria_atual_percent) + (kwh_consumido / float(veiculo.capacidade_bateria_kwh)) * 100,
        100,
    )

    estacao.status = "disponivel"
    estacao.potencia_atual_kw = 0

    db.flush()
    _recalcular_potencia_ativas(db, config)
    _reavaliar_fila(db)
    return sessao


@router.post("/iniciar", response_model=SessaoOut, status_code=status.HTTP_201_CREATED)
def iniciar_sessao(
    dados: SessaoIniciar,
    usuario: Usuario = Depends(obter_usuario_atual),
    db: Session = Depends(get_db),
):
    veiculo = db.get(Veiculo, dados.veiculo_id)
    if not veiculo or veiculo.usuario_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veiculo nao encontrado")

    estacao = db.get(Estacao, dados.estacao_id)
    if not estacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estacao nao encontrada")
    if estacao.status != "disponivel":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Estacao nao esta disponivel")

    sessao_ativa = (
        db.query(Sessao)
        .filter(Sessao.veiculo_id == veiculo.id, Sessao.status == "carregando")
        .first()
    )
    if sessao_ativa:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este veiculo ja possui uma recarga em andamento")

    config = _config(db)

    sessao = Sessao(
        veiculo_id=veiculo.id,
        estacao_id=estacao.id,
        usuario_id=usuario.id,
        limite_percent=dados.limite_percent or float(veiculo.limite_percent_padrao),
        limite_custo=dados.limite_custo if dados.limite_custo is not None else veiculo.limite_custo_padrao,
        status="carregando",
        tarifa_aplicada=tarifa_vigente(
            datetime.now(),
            float(config.tarifa_ponta),
            float(config.tarifa_fora_ponta),
            config.horario_ponta_inicio,
            config.horario_ponta_fim,
        ),
    )
    estacao.status = "ocupada"
    db.add(sessao)
    db.flush()

    _recalcular_potencia_ativas(db, config)
    db.refresh(sessao)

    if float(sessao.potencia_alocada_kw) <= 0.01:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sem potencia disponivel no predio neste momento. Entre na fila de espera.",
        )

    db.commit()
    db.refresh(sessao)
    return sessao


@router.post("/{sessao_id}/parar", response_model=SessaoFinalizadaOut)
def parar_sessao(
    sessao_id: int,
    usuario: Usuario = Depends(obter_usuario_atual),
    db: Session = Depends(get_db),
):
    sessao = db.get(Sessao, sessao_id)
    if not sessao or (sessao.usuario_id != usuario.id and usuario.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessao nao encontrada")
    if sessao.status != "carregando":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sessao ja finalizada")

    config = _config(db)
    sessao = _finalizar_sessao(db, sessao, config, datetime.now())
    db.commit()
    db.refresh(sessao)

    return SessaoFinalizadaOut(
        id=sessao.id,
        status=sessao.status,
        kwh_consumido=float(sessao.kwh_consumido),
        custo_total=float(sessao.custo_total),
        kwh_solar=float(sessao.kwh_solar),
        co2_evitado_kg=float(sessao.co2_evitado_kg),
        mensagem=f"Recarga finalizada - {float(sessao.kwh_consumido):.1f} kWh, R$ {float(sessao.custo_total):.2f}",
    )


@router.get("/ativas", response_model=list[SessaoOut])
def sessoes_ativas(db: Session = Depends(get_db), _usuario: Usuario = Depends(obter_usuario_atual)):
    return db.query(Sessao).filter(Sessao.status == "carregando").all()


@router.get("/status/{sessao_id}", response_model=SessaoStatusOut)
def status_sessao(
    sessao_id: int,
    usuario: Usuario = Depends(obter_usuario_atual),
    db: Session = Depends(get_db),
):
    sessao = db.get(Sessao, sessao_id)
    if not sessao or (sessao.usuario_id != usuario.id and usuario.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessao nao encontrada")

    veiculo = sessao.veiculo
    agora = datetime.now()

    if sessao.status != "carregando":
        return SessaoStatusOut(
            id=sessao.id,
            status=sessao.status,
            bateria_atual_percent=float(veiculo.bateria_atual_percent),
            limite_percent=float(sessao.limite_percent),
            kwh_consumido=float(sessao.kwh_consumido),
            potencia_alocada_kw=float(sessao.potencia_alocada_kw),
            custo_total=float(sessao.custo_total),
            limite_custo=float(sessao.limite_custo) if sessao.limite_custo is not None else None,
            tempo_decorrido_min=round((sessao.fim - sessao.inicio).total_seconds() / 60, 1) if sessao.fim else 0,
            tempo_estimado_restante_min=None,
        )

    config = _config(db)
    horas_decorridas = max((agora - sessao.inicio).total_seconds() / 3600, 0.0)
    kwh_estimado = float(sessao.potencia_alocada_kw) * horas_decorridas

    bateria_inicial = float(veiculo.bateria_atual_percent)
    kwh_maximo_bateria = float(veiculo.capacidade_bateria_kwh) * max(100 - bateria_inicial, 0) / 100
    kwh_estimado = min(kwh_estimado, kwh_maximo_bateria)

    bateria_estimada = min(
        bateria_inicial + (kwh_estimado / float(veiculo.capacidade_bateria_kwh)) * 100, 100
    )
    custo_estimado, _ = calcular_custo_sessao(
        sessao.inicio,
        agora,
        kwh_estimado,
        float(config.tarifa_ponta),
        float(config.tarifa_fora_ponta),
        config.horario_ponta_inicio,
        config.horario_ponta_fim,
    )

    atingiu_limite_percent = bateria_estimada >= float(sessao.limite_percent)
    atingiu_limite_custo = bool(sessao.limite_custo) and custo_estimado >= float(sessao.limite_custo)

    if atingiu_limite_percent or atingiu_limite_custo:
        sessao = _finalizar_sessao(db, sessao, config, agora)
        db.commit()
        db.refresh(sessao)
        return SessaoStatusOut(
            id=sessao.id,
            status=sessao.status,
            bateria_atual_percent=float(veiculo.bateria_atual_percent),
            limite_percent=float(sessao.limite_percent),
            kwh_consumido=float(sessao.kwh_consumido),
            potencia_alocada_kw=float(sessao.potencia_alocada_kw),
            custo_total=float(sessao.custo_total),
            limite_custo=float(sessao.limite_custo) if sessao.limite_custo is not None else None,
            tempo_decorrido_min=round((sessao.fim - sessao.inicio).total_seconds() / 60, 1),
            tempo_estimado_restante_min=0,
        )

    kwh_alvo = float(veiculo.capacidade_bateria_kwh) * (float(sessao.limite_percent) - bateria_inicial) / 100
    kwh_restante = max(kwh_alvo - kwh_estimado, 0)
    tempo_restante_min = (
        round((kwh_restante / float(sessao.potencia_alocada_kw)) * 60, 1)
        if float(sessao.potencia_alocada_kw) > 0
        else None
    )

    return SessaoStatusOut(
        id=sessao.id,
        status=sessao.status,
        bateria_atual_percent=round(bateria_estimada, 1),
        limite_percent=float(sessao.limite_percent),
        kwh_consumido=round(kwh_estimado, 3),
        potencia_alocada_kw=float(sessao.potencia_alocada_kw),
        custo_total=round(custo_estimado, 2),
        limite_custo=float(sessao.limite_custo) if sessao.limite_custo is not None else None,
        tempo_decorrido_min=round(horas_decorridas * 60, 1),
        tempo_estimado_restante_min=tempo_restante_min,
    )


@router.get("/historico", response_model=list[SessaoOut])
def historico_sessoes(
    usuario: Usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)
):
    return (
        db.query(Sessao)
        .filter(Sessao.usuario_id == usuario.id)
        .order_by(Sessao.inicio.desc())
        .all()
    )
