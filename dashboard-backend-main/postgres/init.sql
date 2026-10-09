-- ============================================================
-- Globo2-PE - Schema PostgreSQL
-- Espelha exatamente o schema criado por backend/worker/worker.py
-- e consumido por data_ia/predictor.py. Ver README.md > "Tabelas
-- do PostgreSQL" para a descrição de cada campo.
-- ============================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id           SERIAL PRIMARY KEY,
    nome         TEXT UNIQUE NOT NULL,
    criado_em    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projetos (
    id           SERIAL PRIMARY KEY,
    nome         TEXT        NOT NULL,
    usuario_id   INT         NOT NULL REFERENCES usuarios(id),
    status       TEXT        NOT NULL DEFAULT 'em_andamento',
    concluido_em TIMESTAMPTZ,
    criado_em    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (nome, usuario_id)
);

CREATE TABLE IF NOT EXISTS eventos (
    id           SERIAL PRIMARY KEY,
    tipo         TEXT        NOT NULL,
    caminho      TEXT,
    arquivo      TEXT        NOT NULL,
    pasta        TEXT,
    is_final     BOOLEAN     DEFAULT FALSE,
    usuario_id   INT         REFERENCES usuarios(id),
    projeto_id   INT         REFERENCES projetos(id),
    ocorrido_em  TIMESTAMPTZ NOT NULL,
    inserido_em  TIMESTAMPTZ DEFAULT NOW()
);

-- Usada pela camada de IA (data_ia/predictor.py) para calcular o ETC.
CREATE TABLE IF NOT EXISTS edicoes (
    id                  SERIAL PRIMARY KEY,
    editor              TEXT,
    arquivo             TEXT,
    projeto             TEXT,
    inicio_edicao       TIMESTAMPTZ,
    fim_edicao          TIMESTAMPTZ,
    duracao_segundos    INT,
    tamanho_arquivo_mb  FLOAT,
    inserido_em         TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_projetos_status      ON projetos(status);
CREATE INDEX IF NOT EXISTS idx_eventos_ocorrido_em  ON eventos(ocorrido_em);
CREATE INDEX IF NOT EXISTS idx_eventos_projeto      ON eventos(projeto_id);
CREATE INDEX IF NOT EXISTS idx_edicoes_editor        ON edicoes(editor);
CREATE INDEX IF NOT EXISTS idx_edicoes_fim_edicao     ON edicoes(fim_edicao);
