from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.fila import FilaEspera
from app.models.sessao import Sessao
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.schemas.fila import FilaEntrar, FilaOut, FilaPosicaoOut
from app.security import obter_usuario_atual
from app.services import fila as fila_service

router = APIRouter(prefix="/api/fila", tags=["Fila de espera"])


@router.post("/entrar", response_model=FilaOut, status_code=status.HTTP_201_CREATED)
def entrar_na_fila(
    dados: FilaEntrar,
    usuario: Usuario = Depends(obter_usuario_atual),
    db: Session = Depends(get_db),
):
    veiculo = db.get(Veiculo, dados.veiculo_id)
    if not veiculo or veiculo.usuario_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veiculo nao encontrado")

    ja_carregando = (
        db.query(Sessao)
        .filter(Sessao.veiculo_id == veiculo.id, Sessao.status == "carregando")
        .first()
    )
    if ja_carregando:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este veiculo ja esta carregando")

    ja_na_fila = (
        db.query(FilaEspera)
        .filter(FilaEspera.veiculo_id == veiculo.id, FilaEspera.status.in_(["aguardando", "notificada"]))
        .first()
    )
    if ja_na_fila:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este veiculo ja esta na fila")

    prioridade = fila_service.prioridade_para_fila(float(veiculo.bateria_atual_percent))
    item = FilaEspera(usuario_id=usuario.id, veiculo_id=veiculo.id, prioridade=prioridade, posicao_fila=0)
    db.add(item)
    db.flush()

    aguardando = db.query(FilaEspera).filter(FilaEspera.status == "aguardando").all()
    ordenada = fila_service.reordenar(aguardando)
    for posicao, fila_item in enumerate(ordenada, start=1):
        fila_item.posicao_fila = posicao

    db.commit()
    db.refresh(item)
    return item


@router.get("/posicao", response_model=FilaPosicaoOut)
def posicao_na_fila(usuario: Usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    item = (
        db.query(FilaEspera)
        .filter(FilaEspera.usuario_id == usuario.id, FilaEspera.status.in_(["aguardando", "notificada"]))
        .order_by(FilaEspera.criado_em.desc())
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voce nao esta na fila")

    return FilaPosicaoOut(
        posicao_fila=item.posicao_fila,
        prioridade=item.prioridade,
        pessoas_a_frente=max(item.posicao_fila - 1, 0),
        previsao_espera_min=fila_service.estimar_espera_minutos(item.posicao_fila),
        status=item.status,
    )
