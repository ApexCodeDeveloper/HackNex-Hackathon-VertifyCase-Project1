-- ============================================================================
-- VertifyCase — Chat History DB Upgrade
-- Adds the columns needed by the chat-history panel to the existing
-- `conversations` table. Safe to run on a database that was created with the
-- original schema (which only had conversation_id + created_at).
--
-- HOW TO APPLY:
--   Supabase Dashboard → SQL Editor → paste this file → Run.
--   It is idempotent: running it more than once is harmless.
-- ============================================================================

-- 1) Add the new columns (IF NOT EXISTS makes this re-runnable)
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS title      TEXT;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS updated_at TEXT;

-- 2) Backfill updated_at for rows created before this migration
UPDATE conversations
   SET updated_at = created_at
 WHERE updated_at IS NULL;

-- 3) Give every conversation a visible title
UPDATE conversations
   SET title = 'New conversation'
 WHERE title IS NULL OR title = '';

-- 4) Defaults + index so the history list loads fast and stays sorted
ALTER TABLE conversations
    ALTER COLUMN updated_at SET DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_conversations_updated
    ON conversations (updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages (conversation_id, created_at);

-- 5) (Recommended) auto-cascade message deletion when a conversation is
--    deleted, so the API's delete endpoint needs only one call.
--    If a foreign key with ON DELETE CASCADE already exists this is a no-op.
DO $$
BEGIN
    ALTER TABLE messages
        DROP CONSTRAINT IF EXISTS messages_conversation_id_fkey;
    ALTER TABLE messages
        ADD CONSTRAINT messages_conversation_id_fkey
        FOREIGN KEY (conversation_id)
        REFERENCES conversations(conversation_id)
        ON DELETE CASCADE;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not add cascade FK (non-fatal): %', SQLERRM;
END $$;
