-- intel-agent schema
-- PostgreSQL 16

CREATE TABLE IF NOT EXISTS sources (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,          -- 'hackernews', 'github', 'arxiv', etc.
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    last_run    TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS items (
    id          SERIAL PRIMARY KEY,
    source_id   INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    external_id TEXT NOT NULL,
    title       TEXT NOT NULL,
    url         TEXT,
    description TEXT,
    category    TEXT,
    published_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_source_item UNIQUE (source_id, external_id)
);

-- indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_items_source    ON items (source_id);
CREATE INDEX IF NOT EXISTS idx_items_category  ON items (category);
CREATE INDEX IF NOT EXISTS idx_items_collected ON items (collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_items_published ON items (published_at DESC);
