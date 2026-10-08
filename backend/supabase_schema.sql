-- ============================================================================
-- VertifyCase — Base Supabase schema (fresh install)
--
-- Run this ONCE in a brand-new Supabase project:
--   Supabase Dashboard → SQL Editor → paste this file → Run.
--
-- If you already have an older install, run supabase_migration.sql instead
-- (it upgrades the existing tables without touching your data).
-- ============================================================================

-- Documents ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    document_id   TEXT PRIMARY KEY,
    document_name TEXT NOT NULL,
    file_path     TEXT NOT NULL,
    file_size     INTEGER NOT NULL,
    page_count    INTEGER NOT NULL,
    chunk_count   INTEGER NOT NULL,
    created_at    TEXT NOT NULL
);

-- Conversations (chat history) ----------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    title           TEXT,
    updated_at      TEXT NOT NULL DEFAULT to_char(now() AT TIME ZONE 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
);

CREATE INDEX IF NOT EXISTS idx_conversations_updated
    ON conversations (updated_at DESC);

-- Messages -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    message_id      TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    metadata        JSONB,
    created_at      TEXT NOT NULL,
    CONSTRAINT messages_conversation_id_fkey
        FOREIGN KEY (conversation_id)
        REFERENCES conversations (conversation_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages (conversation_id, created_at);
