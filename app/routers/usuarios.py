from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.config import ConfigPredio
from app.models.movimentacao_saldo import MovimentacaoSaldo
from app.models.sessao import Sessao
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.schemas.usuario import (
    PremiarUsuarioIn,
    PremiarUsuarioOut,
    UsuarioAdminOut,
    UsuariosResumoOut,
)
from app.security import exigir_admin
from app.services.tarifacao import tarifa_vigente

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


@router.post("/{usuario_id}/premiar", response_model=PremiarUsuarioOut)
def premiar_usuario(
    usuario_id: int,
    dados: PremiarUsuarioIn,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_admin),
):
    """Credita saldo na conta do usuario como premio/beneficio (ex: recarga
    gratis para o maior consumidor do periodo). O credito e apenas um bonus de
    saldo - nao mexe em tarifa nem em nenhuma sessao."""
    usuario = db.get(Usuario, usuario_id)
    if not usuario or usuario.role != "usuario":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    usuario.saldo = float(usuario.saldo) + dados.valor
    db.add(
        MovimentacaoSaldo(
            usuario_id=usuario.id,
            tipo="recarga",
            valor=dados.valor,
            saldo_apos=usuario.saldo,
            descricao=dados.motivo or "Prêmio: maior consumidor do período",
        )
    )
    db.commit()
    db.refresh(usuario)

    return PremiarUsuarioOut(
        usuario_id=usuario.id,
        saldo_atual=float(usuario.saldo),
        mensagem=f"{usuario.nome} recebeu R$ {dados.valor:.2f} de crédito.",
    )


@router.post("/{usuario_id}/premiar-recarga-gratis", response_model=PremiarUsuarioOut)
def premiar_recarga_gratis(
    usuario_id: int,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_admin),
):
    """Calcula quanto custaria carregar o veiculo do usuario ate 100% na
    tarifa vigente agora, e credita exatamente esse valor no saldo dele -
    uma recarga completa de graca, em vez de um valor arbitrario."""
    usuario = db.get(Usuario, usuario_id)
    if not usuario or usuario.role != "usuario":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    veiculos = db.query(Veiculo).filter(Veiculo.usuario_id == usuario.id).all()
    if not veiculos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este usuário não tem veículo cadastrado para calcular a recarga grátis.",
        )

    # Usa o veiculo com a bateria mais baixa - quem mais precisa de carga.
    veiculo = min(veiculos, key=lambda v: float(v.bateria_atual_percent))

    config = db.query(ConfigPredio).first()
    if not config:
        raise HTTPException(status_code=500, detail="Configuração do prédio não encontrada")

    kwh_necessario = float(veiculo.capacidade_bateria_kwh) * max(
        100 - float(veiculo.bateria_atual_percent), 0
    ) / 100
    tarifa_atual = tarifa_vigente(
        datetime.now(),
        float(config.tarifa_pico),
        float(config.tarifa_fora_pico),
        config.horario_pico_inicio,
        config.horario_pico_fim,
    )
    valor_credito = round(kwh_necessario * tarifa_atual, 2)
    if valor_credito <= 0:
        valor_credito = round(float(config.tarifa_fora_pico) * 5, 2)  # bateria ja em 100%, da um minimo simbolico

    usuario.saldo = float(usuario.saldo) + valor_credito
    db.add(
        MovimentacaoSaldo(
            usuario_id=usuario.id,
            tipo="recarga",
            valor=valor_credito,
            saldo_apos=usuario.saldo,
            descricao=f"Prêmio: recarga grátis completa do veículo {veiculo.placa}",
        )
    )
    db.commit()
    db.refresh(usuario)

    return PremiarUsuarioOut(
        usuario_id=usuario.id,
        saldo_atual=float(usuario.saldo),
        mensagem=f"{usuario.nome} ganhou uma recarga grátis completa (R$ {valor_credito:.2f}) para o {veiculo.placa}.",
    )
