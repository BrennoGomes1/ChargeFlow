from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.schemas.veiculo import VeiculoCreate, VeiculoOut
from app.security import obter_usuario_atual

router = APIRouter(prefix="/api/veiculos", tags=["Veiculos"])


@router.get("", response_model=list[VeiculoOut])
def listar_veiculos(
    usuario: Usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)
):
    return db.query(Veiculo).filter(Veiculo.usuario_id == usuario.id).all()


@router.post("", response_model=VeiculoOut, status_code=status.HTTP_201_CREATED)
def cadastrar_veiculo(
    dados: VeiculoCreate,
    usuario: Usuario = Depends(obter_usuario_atual),
    db: Session = Depends(get_db),
):
    ja_existe = (
        db.query(Veiculo)
        .filter(Veiculo.usuario_id == usuario.id, Veiculo.placa == dados.placa)
        .first()
    )
    if ja_existe:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Veiculo com essa placa ja cadastrado")

    veiculo = Veiculo(usuario_id=usuario.id, **dados.model_dump())
    db.add(veiculo)
    db.commit()
    db.refresh(veiculo)
    return veiculo
