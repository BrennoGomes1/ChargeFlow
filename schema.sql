-- ChargeFlow - Schema PostgreSQL
-- Sistema de recarga inteligente para veiculos eletricos em predios comerciais

DROP TABLE IF EXISTS fila_espera CASCADE;
DROP TABLE IF EXISTS sessoes CASCADE;
DROP TABLE IF EXISTS config_predio CASCADE;
DROP TABLE IF EXISTS estacoes CASCADE;
DROP TABLE IF EXISTS veiculos CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- =========================================================
-- usuarios
-- =========================================================
CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(120) NOT NULL,
    email           VARCHAR(180) NOT NULL UNIQUE,
    senha_hash      VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'usuario' CHECK (role IN ('usuario', 'admin')),
    empresa         VARCHAR(120),
    telefone        VARCHAR(30),
    criado_em       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =========================================================
-- veiculos
-- =========================================================
CREATE TABLE veiculos (
    id                          SERIAL PRIMARY KEY,
    usuario_id                  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    placa                       VARCHAR(10) NOT NULL,
    modelo                      VARCHAR(80) NOT NULL,
    marca                       VARCHAR(80),
    capacidade_bateria_kwh      NUMERIC(6, 2) NOT NULL CHECK (capacidade_bateria_kwh > 0),
    bateria_atual_percent       NUMERIC(5, 2) NOT NULL DEFAULT 0 CHECK (bateria_atual_percent BETWEEN 0 AND 100),
    limite_percent_padrao       NUMERIC(5, 2) NOT NULL DEFAULT 80 CHECK (limite_percent_padrao BETWEEN 1 AND 100),
    limite_custo_padrao         NUMERIC(10, 2) DEFAULT 50,
    criado_em                   TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (usuario_id, placa)
);

-- =========================================================
-- estacoes
-- =========================================================
CREATE TABLE estacoes (
    id                  SERIAL PRIMARY KEY,
    nome                VARCHAR(80) NOT NULL UNIQUE,
    potencia_max_kw     NUMERIC(6, 2) NOT NULL CHECK (potencia_max_kw > 0),
    potencia_atual_kw   NUMERIC(6, 2) NOT NULL DEFAULT 0,
    status              VARCHAR(20) NOT NULL DEFAULT 'disponivel'
                            CHECK (status IN ('disponivel', 'ocupada', 'manutencao', 'offline')),
    localizacao         VARCHAR(120)
);

-- =========================================================
-- config_predio (linha unica de configuracao global)
-- =========================================================
CREATE TABLE config_predio (
    id                          SERIAL PRIMARY KEY,
    potencia_max_total_kw       NUMERIC(7, 2) NOT NULL CHECK (potencia_max_total_kw > 0),
    tarifa_pico                NUMERIC(6, 4) NOT NULL,
    tarifa_fora_pico           NUMERIC(6, 4) NOT NULL,
    horario_pico_inicio        TIME NOT NULL DEFAULT '17:00',
    horario_pico_fim           TIME NOT NULL DEFAULT '22:00',
    percentual_solar            NUMERIC(5, 2) NOT NULL DEFAULT 30 CHECK (percentual_solar BETWEEN 0 AND 100)
);

-- =========================================================
-- sessoes
-- =========================================================
CREATE TABLE sessoes (
    id                      SERIAL PRIMARY KEY,
    veiculo_id              INTEGER NOT NULL REFERENCES veiculos(id) ON DELETE CASCADE,
    estacao_id              INTEGER NOT NULL REFERENCES estacoes(id) ON DELETE CASCADE,
    usuario_id              INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    limite_percent          NUMERIC(5, 2) NOT NULL DEFAULT 80,
    limite_custo            NUMERIC(10, 2),
    inicio                  TIMESTAMP NOT NULL DEFAULT NOW(),
    fim                     TIMESTAMP,
    kwh_consumido           NUMERIC(8, 3) NOT NULL DEFAULT 0,
    potencia_alocada_kw     NUMERIC(6, 2) NOT NULL DEFAULT 0,
    custo_total             NUMERIC(10, 2) NOT NULL DEFAULT 0,
    tarifa_aplicada         NUMERIC(6, 4),
    status                  VARCHAR(20) NOT NULL DEFAULT 'carregando'
                                CHECK (status IN ('carregando', 'finalizada', 'cancelada', 'na_fila')),
    kwh_solar               NUMERIC(8, 3) NOT NULL DEFAULT 0,
    co2_evitado_kg          NUMERIC(8, 3) NOT NULL DEFAULT 0
);

CREATE INDEX idx_sessoes_status ON sessoes(status);
CREATE INDEX idx_sessoes_usuario ON sessoes(usuario_id);

-- =========================================================
-- fila_espera
-- =========================================================
CREATE TABLE fila_espera (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    veiculo_id      INTEGER NOT NULL REFERENCES veiculos(id) ON DELETE CASCADE,
    prioridade      VARCHAR(10) NOT NULL CHECK (prioridade IN ('ALTA', 'MEDIA', 'BAIXA')),
    posicao_fila    INTEGER NOT NULL,
    criado_em       TIMESTAMP NOT NULL DEFAULT NOW(),
    status          VARCHAR(20) NOT NULL DEFAULT 'aguardando'
                        CHECK (status IN ('aguardando', 'notificada', 'atendida', 'cancelada'))
);

CREATE INDEX idx_fila_status ON fila_espera(status);