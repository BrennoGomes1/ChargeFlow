-- ChargeFlow - Dados de teste (seed)
-- Senha de todos os usuarios de teste: "senha123"
-- Hash bcrypt gerado com passlib (custo padrao)

-- =========================================================
-- config_predio
-- =========================================================
INSERT INTO config_predio (potencia_max_total_kw, tarifa_ponta, tarifa_fora_ponta, horario_ponta_inicio, horario_ponta_fim, percentual_solar)
VALUES (150.00, 1.25, 0.75, '17:00', '22:00', 30.00);

-- =========================================================
-- usuarios
-- senha_hash abaixo = bcrypt("senha123")
-- =========================================================
INSERT INTO usuarios (nome, email, senha_hash, role, empresa, telefone) VALUES
('Admin ChargeFlow', 'admin@chargeflow.com',   '$2b$12$x.KMmceuApSvD6BH56Q7Ku13nkTXzjuxRzzo3wkewjq02WzJKtF8S', 'admin',   'ChargeFlow',      '11999990000'),
('Ana Souza',        'ana.souza@techcorp.com', '$2b$12$x.KMmceuApSvD6BH56Q7Ku13nkTXzjuxRzzo3wkewjq02WzJKtF8S', 'usuario', 'TechCorp',        '11988881111'),
('Bruno Lima',       'bruno.lima@innova.com',  '$2b$12$x.KMmceuApSvD6BH56Q7Ku13nkTXzjuxRzzo3wkewjq02WzJKtF8S', 'usuario', 'Innova Ltda',     '11988882222'),
('Carla Dias',       'carla.dias@techcorp.com','$2b$12$x.KMmceuApSvD6BH56Q7Ku13nkTXzjuxRzzo3wkewjq02WzJKtF8S', 'usuario', 'TechCorp',        '11988883333'),
('Diego Ferreira',   'diego.f@grupoalfa.com',  '$2b$12$x.KMmceuApSvD6BH56Q7Ku13nkTXzjuxRzzo3wkewjq02WzJKtF8S', 'usuario', 'Grupo Alfa',      '11988884444'),
('Elisa Martins',    'elisa.m@innova.com',     '$2b$12$x.KMmceuApSvD6BH56Q7Ku13nkTXzjuxRzzo3wkewjq02WzJKtF8S', 'usuario', 'Innova Ltda',     '11988885555');

-- =========================================================
-- veiculos
-- =========================================================
INSERT INTO veiculos (usuario_id, placa, modelo, marca, capacidade_bateria_kwh, bateria_atual_percent, limite_percent_padrao, limite_custo_padrao) VALUES
(2, 'ABC1D23', 'Model 3',   'Tesla',      60.0, 22.0, 80, 50.00),
(3, 'BRA2E19', 'Leaf',      'Nissan',     40.0, 65.0, 90, 40.00),
(4, 'FLA4X56', 'ID.4',      'Volkswagen', 77.0, 18.0, 80, 60.00),
(5, 'MER5Y88', 'Kona EV',   'Hyundai',    64.0, 85.0, 80, 30.00),
(6, 'ZUL9K12', 'Bolt EUV',  'Chevrolet',  65.0, 45.0, 85, 45.00);

-- =========================================================
-- estacoes
-- =========================================================
INSERT INTO estacoes (nome, potencia_max_kw, potencia_atual_kw, status, localizacao) VALUES
('Estacao A1', 50.00, 0, 'disponivel', 'Subsolo 1 - Vaga 01'),
('Estacao A2', 50.00, 0, 'disponivel', 'Subsolo 1 - Vaga 03'),
('Estacao A3', 50.00, 0, 'disponivel', 'Subsolo 1 - Vaga 05'),
('Estacao B1', 22.00, 0, 'disponivel', 'Subsolo 2 - Vaga 10'),
('Estacao B2', 22.00, 0, 'manutencao', 'Subsolo 2 - Vaga 11'),
('Estacao C1', 11.00, 0, 'disponivel', 'Terreo - Vaga 01');

-- =========================================================
-- sessoes (historico de exemplo, ja finalizadas)
-- =========================================================
INSERT INTO sessoes (veiculo_id, estacao_id, usuario_id, limite_percent, limite_custo, inicio, fim, kwh_consumido, potencia_alocada_kw, custo_total, tarifa_aplicada, status, kwh_solar, co2_evitado_kg) VALUES
(2, 1, 3, 90, 40.00, NOW() - INTERVAL '2 days' - INTERVAL '3 hours', NOW() - INTERVAL '2 days' - INTERVAL '2 hours', 18.500, 22.00, 13.88, 0.75, 'finalizada', 5.550, 0.4535),
(1, 4, 2, 80, 50.00, NOW() - INTERVAL '1 days' - INTERVAL '5 hours', NOW() - INTERVAL '1 days' - INTERVAL '4 hours', 12.000, 12.00, 15.00, 1.25, 'finalizada', 3.600, 0.2941),
(3, 2, 4, 80, 60.00, NOW() - INTERVAL '20 hours', NOW() - INTERVAL '18 hours', 25.300, 12.65, 18.98, 0.75, 'finalizada', 7.590, 0.6202);

-- =========================================================
-- fila_espera (vazia por padrao, populada em tempo real pelo sistema)
-- =========================================================
