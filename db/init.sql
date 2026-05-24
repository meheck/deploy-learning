CREATE TABLE jobs (
    id          UUID        PRIMARY KEY,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending',
    input       TEXT        NOT NULL,
    output      JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);