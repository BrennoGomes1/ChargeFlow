from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sessao import Sessao
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.schemas.usuario import UsuarioAdminOut, UsuariosResumoOut
from app.security import exigir_admin

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios (Admin)"])


@router.get("", response_model=UsuariosResumoOut)
def listar_usuarios(db: Session = Depends(get_db), _admin: Usuario = Depends(exigir_admin)):
    usuarios = (
        db.query(Usuario).filter(Usuario.role == "usuario").order_by(Usuario.criado_em.desc()).all()
    )

    resultado = []
    empresas = set()
    for u in usuarios:
        if u.empresa:
            empresas.add(u.empresa)

        qtd_veiculos = db.query(Veiculo).filter(Veiculo.usuario_id == u.id).count()
        qtd_sessoes = (
            db.query(Sessao)
            .filter(Sessao.usuario_id == u.id, Sessao.status == "finalizada")
            .count()
        )
        resultado.append(
            UsuarioAdminOut(
                id=u.id,
                nome=u.nome,
                email=u.email,
                empresa=u.empresa,
                telefone=u.telefone,
                saldo=float(u.saldo),
                qtd_veiculos=qtd_veiculos,
                qtd_sessoes_finalizadas=qtd_sessoes,
                criado_em=u.criado_em,
            )
        )

    return UsuariosResumoOut(
        total_usuarios=len(resultado),
        total_empresas=len(empresas),
        usuarios=resultado,
    )
