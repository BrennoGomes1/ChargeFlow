# ChargeFlow

Sistema de recarga inteligente para veiculos eletricos em predios comerciais.

Projeto desenvolvido para o desafio GoodWe — FIAP 2026, com foco em classificacao
para o NEXT FIAP 2026.

## O problema

Predios comerciais que oferecem recarga para veiculos eletricos enfrentam tres
desafios: controlar a demanda de potencia para nao estourar o limite do predio,
cobrar de forma justa cada usuario pelo que consumiu, e oferecer uma experiencia
pratica para o motorista que chega e precisa carregar.

## A solucao

- **Distribuicao inteligente de potencia** — algoritmo de water-filling que
  reparte a potencia disponivel do predio entre os carros conectados,
  priorizando quem esta com bateria mais baixa e reduzindo a potencia geral em
  horario de ponta.
- **Cobranca automatica** — cada sessao registra kWh consumido, horario (ponta
  ou fora de ponta) e calcula o custo automaticamente, com corte quando o
  usuario atinge seu limite de % ou de gasto.
- **Fila inteligente** — quando todas as estacoes estao ocupadas, o motorista
  entra numa fila ordenada por prioridade e recebe uma previsao de espera.
- **Sustentabilidade** — cada sessao calcula quanto da energia veio de fontes
  solares e o CO2 evitado (fator de emissao do SIN: 0.0817 kg/kWh).
- **Dashboard visual** — app mobile para o motorista e painel desktop para o
  administrador do predio, com simulacao de cenarios ao vivo.

## Stack tecnica

| Camada | Tecnologia |
|---|---|
| Back-end | Python + FastAPI + SQLAlchemy + JWT (python-jose) |
| Banco de dados | PostgreSQL |
| Front-end | HTML/CSS/JS puro + Chart.js |

## Estrutura do projeto

```
chargeflow/
├── app/
│   ├── main.py              # FastAPI app principal
│   ├── database.py          # Conexao com PostgreSQL
│   ├── security.py          # Hash de senha, JWT, dependencias de autenticacao
│   ├── models/               # Modelos SQLAlchemy (tabelas)
│   ├── schemas/               # Schemas Pydantic (validacao)
│   ├── routers/               # Endpoints da API
│   └── services/               # Logica de negocio
│       ├── potencia.py        # Algoritmo de distribuicao inteligente (water-filling)
│       ├── priorizacao.py     # Regras de prioridade por bateria
│       ├── tarifacao.py       # Calculo de custo ponta/fora de ponta
│       ├── sustentabilidade.py # CO2 evitado, % solar
│       └── fila.py            # Gerenciamento de fila
├── frontend/
│   ├── usuario/               # Visao mobile do usuario
│   └── admin/                 # Visao desktop do admin
├── schema.sql                 # DDL do banco
├── seed.sql                   # Dados de teste
├── requirements.txt
└── .env.example
```

## Como rodar

### 1. Banco de dados

Crie um banco PostgreSQL e rode o schema e o seed:

```bash
createdb chargeflow
psql -d chargeflow -f schema.sql
psql -d chargeflow -f seed.sql
```

### 2. Back-end

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

copy .env.example .env          # e ajuste DATABASE_URL / JWT_SECRET_KEY
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`. Documentacao automatica (Swagger) em
`http://localhost:8000/docs`.

### 3. Front-end

Os arquivos em `frontend/usuario` e `frontend/admin` sao HTML/CSS/JS estaticos —
basta abrir `index.html` num servidor estatico local (ex: extensao "Live Server"
do VS Code, ou `python -m http.server` dentro de cada pasta) enquanto o back-end
roda em paralelo. Por padrao o front-end aponta para `http://localhost:8000`
(ajuste a constante `API_BASE` em `js/app.js` / `js/api.js` se necessario).

**Usuarios de teste (seed.sql)** — senha `senha123` para todos:

| Email | Papel |
|---|---|
| admin@chargeflow.com | admin (painel desktop) |
| ana.souza@techcorp.com | usuario (app mobile) |
| bruno.lima@innova.com | usuario |

## Logica do algoritmo de potencia

1. Calcula a potencia efetiva do predio (reduz 20% em horario de ponta, 17h–22h).
2. Cada carro ativo pede ate a potencia maxima da sua estacao.
3. A potencia disponivel e distribuida por *water-filling* ponderado por
   prioridade: bateria < 30% pesa 3x, 30–70% pesa 2x, > 70% pesa 1x — quem
   satura o proprio teto sai da rodada e o resto e redistribuido entre os
   demais.
4. Se a estacao escolhida nao tiver potencia disponivel no momento, o veiculo
   entra na fila de espera ordenada por prioridade.
5. Ao final de cada sessao, a potencia liberada e redistribuida entre as
   sessoes ativas e a fila e reavaliada.

## Endpoints principais

Veja a lista completa e interativa em `/docs`. Resumo:

- `POST /api/auth/registrar`, `POST /api/auth/login`
- `GET/POST /api/veiculos`
- `GET /api/estacoes`, `GET /api/estacoes/potencia`
- `POST /api/acesso/entrada`, `POST /api/acesso/saida`
- `POST /api/sessoes/iniciar`, `POST /api/sessoes/{id}/parar`,
  `GET /api/sessoes/ativas`, `GET /api/sessoes/status/{id}`,
  `GET /api/sessoes/historico`
- `POST /api/fila/entrar`, `GET /api/fila/posicao`
- `POST /api/simulacao/cenario`, `GET /api/simulacao/potencia-tempo-real`
- `GET /api/dashboard/consumo`, `GET /api/dashboard/sustentabilidade`,
  `GET /api/dashboard/ranking` (somente admin)

## Checklist para o Next

- [x] Back-end FastAPI completo (auth, veiculos, estacoes, sessoes, fila, simulacao, dashboard)
- [x] Algoritmo de potencia com priorizacao por bateria e reducao em horario de ponta
- [x] Calculo de tarifa ponta/fora de ponta e de CO2 evitado
- [x] App mobile do usuario (liberar entrada, iniciar recarga, status em tempo real, historico)
- [x] Painel admin (mapa de vagas, barra de potencia, graficos, simulacao de cenario, ranking)
- [ ] Popular o banco com dados reais/mais realistas para a demo
- [ ] Ensaiar o pitch: problema → solucao → demo ao vivo → impacto
