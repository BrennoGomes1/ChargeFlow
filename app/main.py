import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import acesso, auth, dashboard, estacoes, fila, saldo, sessoes, simulacao, veiculos

load_dotenv()

app = FastAPI(
    title="ChargeFlow API",
    description="Sistema de recarga inteligente para veículos elétricos em prédios comerciais",
    version="1.0.0",
)

origens = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
# Regex opcional (ex: dominios de tunel temporario tipo *.trycloudflare.com,
# que mudam a cada execucao e nao dariam pra listar em CORS_ORIGINS).
origem_regex = os.getenv("CORS_ORIGIN_REGEX") or None
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens or ["*"],
    allow_origin_regex=origem_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(veiculos.router)
app.include_router(estacoes.router)
app.include_router(acesso.router)
app.include_router(sessoes.router)
app.include_router(fila.router)
app.include_router(simulacao.router)
app.include_router(dashboard.router)
app.include_router(saldo.router)


@app.get("/", tags=["Status"])
def raiz():
    return {"status": "ok", "servico": "ChargeFlow API"}
