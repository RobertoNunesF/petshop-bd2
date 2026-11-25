-- =============================================================
-- Script do banco relacional (PostgreSQL) - Petshop
-- Como executar: veja o README.md
-- =============================================================

-- Apaga as tabelas se já existirem (ordem inversa por causa das FKs)
DROP TABLE IF EXISTS pagamentos;
DROP TABLE IF EXISTS agendamentos;
DROP TABLE IF EXISTS servicos;
DROP TABLE IF EXISTS pets;
DROP TABLE IF EXISTS tutores;

-- -------------------------------------------------------------
-- TUTORES
-- cpf guardado só com os 11 dígitos (sem ponto e traço)
-- -------------------------------------------------------------
CREATE TABLE tutores (
    id       SERIAL PRIMARY KEY,
    nome     VARCHAR(100) NOT NULL,
    cpf      CHAR(11)     NOT NULL UNIQUE CHECK (cpf ~ '^[0-9]{11}$'),
    email    VARCHAR(150) NOT NULL UNIQUE,
    telefone VARCHAR(20)
);

-- -------------------------------------------------------------
-- PETS (1 tutor tem N pets -> FK fica em pets)
-- Muitos tutores não sabem a data de nascimento, então guardamos a
-- idade informada + a data em que foi informada. A idade atual é
-- calculada: idade_informada + anos passados desde idade_informada_em
-- -------------------------------------------------------------
CREATE TABLE pets (
    id                 SERIAL PRIMARY KEY,
    tutor_id           INTEGER     NOT NULL REFERENCES tutores(id),
    nome               VARCHAR(60) NOT NULL,
    especie            VARCHAR(30) NOT NULL,
    raca               VARCHAR(60),
    idade_informada    INTEGER     CHECK (idade_informada BETWEEN 0 AND 40),
    idade_informada_em DATE        NOT NULL DEFAULT CURRENT_DATE
);

-- -------------------------------------------------------------
-- SERVICOS (catálogo: banho, tosa, consulta...)
-- -------------------------------------------------------------
CREATE TABLE servicos (
    id           SERIAL PRIMARY KEY,
    procedimento VARCHAR(60)   NOT NULL UNIQUE,
    duracao_min  INTEGER       NOT NULL CHECK (duracao_min > 0),
    valor        NUMERIC(10,2) NOT NULL CHECK (valor >= 0)
);

-- -------------------------------------------------------------
-- AGENDAMENTOS (liga pet + serviço)
-- -------------------------------------------------------------
CREATE TABLE agendamentos (
    id         SERIAL PRIMARY KEY,
    pet_id     INTEGER     NOT NULL REFERENCES pets(id),
    servico_id INTEGER     NOT NULL REFERENCES servicos(id),
    data_hora  TIMESTAMP   NOT NULL,
    status     VARCHAR(20) NOT NULL DEFAULT 'agendado'
               CHECK (status IN ('agendado', 'concluido', 'cancelado'))
);

-- -------------------------------------------------------------
-- PAGAMENTOS (1 agendamento tem 1 pagamento -> agendamento_id UNIQUE)
-- -------------------------------------------------------------
CREATE TABLE pagamentos (
    id              SERIAL PRIMARY KEY,
    agendamento_id  INTEGER       NOT NULL UNIQUE REFERENCES agendamentos(id),
    valor           NUMERIC(10,2) NOT NULL CHECK (valor >= 0),
    forma_pagamento VARCHAR(10)   NOT NULL
                    CHECK (forma_pagamento IN ('dinheiro', 'pix', 'cartao')),
    data_pagamento  TIMESTAMP     NOT NULL DEFAULT NOW()
);

-- =============================================================
-- INSERTs de exemplo para a demonstração
-- (tabelas recém-criadas, então os ids saem 1, 2, 3... na ordem)
-- =============================================================

INSERT INTO tutores (nome, cpf, email, telefone) VALUES
    ('Ana Souza',      '12345678901', 'ana.souza@email.com',    '(51) 99999-1111'),
    ('Bruno Lima',     '23456789012', 'bruno.lima@email.com',   '(51) 99999-2222'),
    ('Carla Martins',  '34567890123', 'carla.martins@email.com','(51) 99999-3333');

-- Thor e Bob foram cadastrados há alguns anos: a idade atual já
-- aparece maior que a informada (Thor: 4 + 2 = 6 anos)
INSERT INTO pets (tutor_id, nome, especie, raca, idade_informada, idade_informada_em) VALUES
    (1, 'Thor', 'cachorro', 'Golden Retriever', 4, CURRENT_DATE - INTERVAL '2 years'),  -- id 1
    (1, 'Mia',  'gato',     'Siamês',           4, CURRENT_DATE),                       -- id 2
    (2, 'Bob',  'cachorro', 'Vira-lata',        5, CURRENT_DATE - INTERVAL '2 years'),  -- id 3
    (3, 'Luna', 'cachorro', 'Shih Tzu',         5, CURRENT_DATE),                       -- id 4
    (3, 'Nina', 'gato',     'Persa',            NULL, CURRENT_DATE);                    -- id 5 (idade desconhecida)

INSERT INTO servicos (procedimento, duracao_min, valor) VALUES
    ('banho',    60, 60.00),   -- id 1
    ('tosa',     90, 80.00),   -- id 2
    ('consulta', 30, 150.00);  -- id 3

-- Datas relativas a hoje (CURRENT_DATE): o script funciona em qualquer dia
-- que for executado. Os concluídos ficam no próprio dia, assim os
-- pagamentos sempre caem no mês atual.
INSERT INTO agendamentos (pet_id, servico_id, data_hora, status) VALUES
    (1, 1, CURRENT_DATE + TIME '08:00',                     'concluido'),  -- id 1
    (1, 3, CURRENT_DATE + TIME '09:00',                     'concluido'),  -- id 2
    (2, 3, CURRENT_DATE + TIME '10:00',                     'concluido'),  -- id 3
    (3, 2, CURRENT_DATE + TIME '11:00',                     'concluido'),  -- id 4
    (4, 1, CURRENT_DATE - INTERVAL '2 days' + TIME '14:00', 'cancelado'),  -- id 5
    (4, 2, CURRENT_DATE + INTERVAL '7 days' + TIME '09:00', 'agendado'),   -- id 6
    (5, 1, CURRENT_DATE + INTERVAL '9 days' + TIME '16:00', 'agendado');   -- id 7

-- Só agendamentos concluídos têm pagamento (30 min depois do atendimento)
INSERT INTO pagamentos (agendamento_id, valor, forma_pagamento, data_pagamento) VALUES
    (1,  60.00, 'pix',      CURRENT_DATE + TIME '08:30'),
    (2, 150.00, 'cartao',   CURRENT_DATE + TIME '09:30'),
    (3, 150.00, 'dinheiro', CURRENT_DATE + TIME '10:30'),
    (4,  80.00, 'pix',      CURRENT_DATE + TIME '11:30');

-- =============================================================
-- CONSULTA DE EXEMPLO (JOIN com as 5 tabelas)
-- Pagamentos do mês atual com nome do tutor, nome do pet e serviço.
-- DATE_TRUNC('month', CURRENT_DATE) = dia 1 do mês de hoje
-- =============================================================
SELECT
    pg.data_pagamento,
    t.nome          AS tutor,
    p.nome          AS pet,
    s.procedimento  AS servico,
    pg.valor,
    pg.forma_pagamento
FROM pagamentos   pg
JOIN agendamentos a ON a.id = pg.agendamento_id
JOIN pets         p ON p.id = a.pet_id
JOIN tutores      t ON t.id = p.tutor_id
JOIN servicos     s ON s.id = a.servico_id
WHERE pg.data_pagamento >= DATE_TRUNC('month', CURRENT_DATE)
  AND pg.data_pagamento <  DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
ORDER BY pg.data_pagamento;
