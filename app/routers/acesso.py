from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.estacao import Estacao
from app.models.usuario import Usuario
from app.schemas.acesso import EntradaOut, SaidaOut
from app.security import obter_usuario_atual

router = APIRouter(prefix="/api/acesso", tags=["Acesso ao predio"])


@router.post("/entrada", response_model=EntradaOut)
def liberar_entrada(usuario: Usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    estacao = (
        db.query(Estacao).filter(Estacao.status == "disponivel").order_by(Estacao.nome).first()
    )
    if estacao:
        return EntradaOut(
            liberado=True,
            mensagem=f"Cancela liberada. Vá para {estacao.nome} - {estacao.localizacao}",
            estacao_sugerida=estacao.nome,
        )

    return EntradaOut(
        liberado=True,
        mensagem="Cancela liberada, mas todas as estações estão ocupadas no momento. Entre na fila pelo app.",
        estacao_sugerida=None,
    )


@router.post("/saida", response_model=SaidaOut)
def liberar_saida(usuario: Usuario = Depends(obter_usuario_atual)):
    return SaidaOut(liberado=True, mensagem="Cancela de saída liberada. Até a próxima!")
