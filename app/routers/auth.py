from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.auth import Token, UsuarioLogin, UsuarioOut, UsuarioRegistrar
from app.security import criar_token_acesso, hash_senha, verificar_senha

router = APIRouter(prefix="/api/auth", tags=["Autenticacao"])


@router.post("/registrar", response_model=Token, status_code=status.HTTP_201_CREATED)
def registrar(dados: UsuarioRegistrar, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == dados.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ja cadastrado")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        empresa=dados.empresa,
        telefone=dados.telefone,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    token = criar_token_acesso(usuario.id)
    return Token(access_token=token, usuario=UsuarioOut.model_validate(usuario))


@router.post("/login", response_model=Token)
def login(dados: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha invalidos")

    token = criar_token_acesso(usuario.id)
    return Token(access_token=token, usuario=UsuarioOut.model_validate(usuario))
