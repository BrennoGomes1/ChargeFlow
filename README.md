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
  horario de pico.
- **Cobranca automatica** — cada sessao registra kWh consumido, horario (pico
  ou fora de pico) e calcula o custo automaticamente, com corte quando o
  usuario atinge seu limite de % ou de gasto.
- **Saldo pre-pago por usuario** — cada usuario tem um saldo proprio que
  recarrega quando quiser. Ao abrir o app ve quanto tem disponivel e ate
  quantos % de bateria isso da pra carregar no veiculo cadastrado; escolhe o
  % desejado e a recarga vai debitando desse saldo ate acabar (ou ate atingir
  o % escolhido), sempre com um extrato de recargas e consumos.
- **Fila inteligente** — quando todas as estacoes estao ocupadas, o motorista
  entra numa fila ordenada por prioridade e recebe uma previsao de espera.
- **Sustentabilidade** — cada sessao calcula quanto da energia veio de fontes
  solares e o CO2 evitado (fator de emissao do SIN: 0.0817 kg/kWh).
- **Dashboard visual** — app mobile para o motorista e painel desktop para o
  administrador do predio, com simulação de cenarios ao vivo.

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
│       ├── tarifacao.py       # Calculo de custo pico/fora de pico
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

## Como rodar (primeira vez, em qualquer PC do time)

Pre-requisitos: **Python 3.11+**, **PostgreSQL 14+** (instalado e rodando como
servico) e **git**.

- Windows: [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
  (o instalador ja sobe o servico automaticamente e pede uma senha para o
  usuario `postgres` — anote essa senha).
- Mac: `brew install postgresql@16 && brew services start postgresql@16`
- Linux (Debian/Ubuntu): `sudo apt install postgresql && sudo systemctl start postgresql`

### 1. Clonar o repositorio

```bash
git clone https://github.com/BrennoGomes1/ChargeFlow.git
cd ChargeFlow
```

### 2. Criar o banco e o usuario do projeto

Rode isto uma vez (vai pedir a senha do super usuário `postgres` que voce
definiu na instalacao):

```bash
psql -U postgres -c "CREATE ROLE chargeflow LOGIN PASSWORD 'chargeflow';"
psql -U postgres -c "CREATE DATABASE chargeflow OWNER chargeflow;"
```

Depois aplique o schema e os dados de teste:

```bash
psql -U chargeflow -d chargeflow -f schema.sql
psql -U chargeflow -d chargeflow -f seed.sql
```

(`schema.sql` comeca com `DROP TABLE IF EXISTS`, entao pode rodar de novo a
qualquer momento para resetar o banco para o estado inicial do seed.)

### 3. Configurar e subir o back-end

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt

copy .env.example .env          # Windows (Mac/Linux: cp .env.example .env)
```

Abra o `.env` criado e confira `DATABASE_URL` — se voce usou o mesmo
usuario/senha do passo 2 (`chargeflow`/`chargeflow`), o valor padrao ja
funciona sem alterar nada. Troque `JWT_SECRET_KEY` por qualquer texto
aleatorio proprio (cada integrante pode ter o seu, so precisa bater entre
subir e usar na mesma maquina).

```bash
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`. Documentacao automatica (Swagger) em
`http://localhost:8000/docs` — bom lugar para testar os endpoints sem
depender do front-end.

### 4. Subir o front-end

O front-end e HTML/CSS/JS puro (sem build). Cada visao precisa rodar num
servidor estatico local — abrir o `index.html` direto no navegador (via
`file://`) nao funciona por causa de CORS. Com o `.venv` ja ativado, abra
**dois terminais novos** (deixando o back-end rodando no primeiro):

```bash
# terminal 2 — app do usuario
cd frontend/usuario
python -m http.server 5500

# terminal 3 — painel admin
cd frontend/admin
python -m http.server 5501
```

Depois acesse:

- App mobile do usuario: `http://localhost:5500`
- Painel admin (desktop): `http://localhost:5501`

Se usar portas diferentes de 5500/5501, adicione-as em `CORS_ORIGINS` no
`.env` (separadas por virgula) e reinicie o `uvicorn`.

**Usuarios de teste (seed.sql)** — senha `senha123` para todos:

| Email | Papel |
|---|---|
| admin@chargeflow.com | admin (painel desktop) |
| ana.souza@techcorp.com | usuario (app mobile) |
| bruno.lima@innova.com | usuario |

## Logica do algoritmo de potencia

1. Calcula a potencia efetiva do predio (reduz 20% em horario de pico, 17h–22h).
2. Cada carro ativo pede ate a potencia maxima da sua estação.
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
- `GET /api/saldo`, `POST /api/saldo/recarregar`,
  `GET /api/saldo/estimativa/{veiculo_id}`, `GET /api/saldo/extrato`
- `POST /api/sessoes/iniciar`, `POST /api/sessoes/{id}/parar`,
  `GET /api/sessoes/ativas`, `GET /api/sessoes/status/{id}`,
  `GET /api/sessoes/historico`
- `POST /api/fila/entrar`, `GET /api/fila/posicao`
- `POST /api/simulacao/cenario`, `GET /api/simulacao/potencia-tempo-real`
- `GET /api/dashboard/consumo`, `GET /api/dashboard/sustentabilidade`,
  `GET /api/dashboard/ranking` (somente admin)

## Checklist para o Next

- [x] Back-end FastAPI completo (auth, veiculos, estacoes, sessoes, fila, simulacao, dashboard)
- [x] Algoritmo de potencia com priorizacao por bateria e reducao em horario de pico
- [x] Calculo de tarifa pico/fora de pico e de CO2 evitado
- [x] App mobile do usuario (liberar entrada, iniciar recarga, status em tempo real, historico)
- [x] Painel admin (mapa de vagas, barra de potencia, graficos, simulacao de cenario, ranking)
- [ ] Popular o banco com dados reais/mais realistas para a demo
- [ ] Ensaiar o pitch: problema → solucao → demo ao vivo → impacto
