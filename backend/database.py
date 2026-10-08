"""Data-access layer for VertifyCase.

Two interchangeable backends, selected automatically from backend/.env:

  1. Supabase (hosted PostgreSQL)
       Active when SUPABASE_URL and SUPABASE_ANON_KEY are both set.
       Tables are created once by pasting supabase_schema.sql into the
       Supabase SQL editor.
  2. SQLite (local fallback)
       Active when those variables are empty — identical behaviour to the
       original database/legal_assistant.db setup.

main.py, documents.py and the frontend always call the same public
functions defined at the bottom of this file, so switching backends
requires no other code changes.
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import DATABASE_PATH, SUPABASE_URL, SUPABASE_ANON_KEY

# Columns the application reads/writes (kept identical across backends)
DOCUMENT_COLUMNS = (
    "document_id", "document_name", "file_path", "file_size",
    "page_count", "chunk_count", "created_at",
)
MESSAGE_COLUMNS = (
    "message_id", "conversation_id", "role", "content", "metadata", "created_at",
)


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class SqliteBackend:
    """Original local store: database/legal_assistant.db (SQLite)."""

    name = "sqlite"

    @property
    def description(self) -> str:
        return DATABASE_PATH

    def init_db(self) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                document_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                page_count INTEGER NOT NULL,
                chunk_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                title TEXT,
                updated_at TEXT
            )
        """)
        # --- Migration: add chat-history columns to pre-existing tables ---
        cursor.execute("PRAGMA table_info(conversations)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "title" not in existing_cols:
            cursor.execute("ALTER TABLE conversations ADD COLUMN title TEXT")
        if "updated_at" not in existing_cols:
            cursor.execute(
                "ALTER TABLE conversations ADD COLUMN updated_at TEXT"
            )
        # Backfill updated_at for any rows created before this migration
        cursor.execute(
            "UPDATE conversations SET updated_at = created_at WHERE updated_at IS NULL"
        )
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation "
            "ON messages(conversation_id, created_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_updated "
            "ON conversations(updated_at DESC)"
        )
        conn.commit()
        conn.close()

    def save_document(self, doc: Dict[str, Any]) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO documents (document_id, document_name, file_path, file_size,
                                   page_count, chunk_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, tuple(doc[c] for c in DOCUMENT_COLUMNS))
        conn.commit()
        conn.close()

    def get_all_documents(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_document(self, document_id: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
        conn.commit()
        conn.close()

    def save_message(
        self,
        conversation_id: str,
        message_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: str = "",
    ) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO conversations (conversation_id, created_at) VALUES (?, ?)",
            (conversation_id, created_at),
        )
        cursor.execute("""
            INSERT INTO messages (message_id, conversation_id, role, content, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            message_id,
            conversation_id,
            role,
            content,
            json.dumps(metadata) if metadata is not None else None,
            created_at,
        ))
        conn.commit()
        conn.close()

    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        results = []
        for r in rows:
            d = dict(r)
            if isinstance(d.get("metadata"), str):
                try:
                    d["metadata"] = json.loads(d["metadata"])
                except Exception:
                    pass
            results.append(d)
        return results

    # --- Conversation history (chat history panel) ---

    def save_conversation(
        self,
        conversation_id: str,
        created_at: str,
        title: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        updated_at = updated_at or created_at
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO conversations (conversation_id, created_at, title, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(conversation_id) DO UPDATE SET
                title = COALESCE(excluded.title, conversations.title),
                updated_at = excluded.updated_at
            """,
            (conversation_id, created_at, title, updated_at),
        )
        conn.commit()
        conn.close()

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE conversation_id = ?",
            (conversation_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.conversation_id, c.created_at, c.title, c.updated_at,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.conversation_id) AS message_count
            FROM conversations c
            ORDER BY COALESCE(c.updated_at, c.created_at) DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()
        results = []
        for r in rows:
            d = dict(r)
            d["title"] = d.get("title") or "New conversation"
            d["updated_at"] = d.get("updated_at") or d.get("created_at")
            results.append(d)
        return results

    def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE conversations
            SET title = COALESCE(?, title),
                updated_at = COALESCE(?, updated_at)
            WHERE conversation_id = ?
            """,
            (title, updated_at, conversation_id),
        )
        conn.commit()
        conn.close()

    def delete_conversation(self, conversation_id: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
        conn.commit()
        conn.close()

    def count_all_stats(self) -> Dict[str, int]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(chunk_count), 0) FROM documents")
        chunk_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT conversation_id) FROM conversations")
        conv_count = cursor.fetchone()[0]
        conn.close()
        return {
            "documents": doc_count,
            "chunks": chunk_count,
            "conversations": conv_count,
        }


class SupabaseBackend:
    """Hosted PostgreSQL via the Supabase client (supabase-py).

    Requires SUPABASE_URL + SUPABASE_ANON_KEY in backend/.env and tables
    created from supabase_schema.sql.
    """

    name = "supabase"

    def __init__(self) -> None:
        self._client = None

    @property
    def description(self) -> str:
        return SUPABASE_URL

    @property
    def client(self):
        # Imported lazily so the SQLite fallback works without supabase installed
        if self._client is None:
            from supabase import create_client
            self._client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        return self._client

    @staticmethod
    def _count_exact():
        from postgrest.types import CountMethod
        return CountMethod.exact

    def init_db(self) -> None:
        # Tables live in Supabase (created via supabase_schema.sql); just verify reachability.
        try:
            self.client.table("documents").select("document_id").limit(1).execute()
            print("[db] Supabase reachable; tables present.")
        except Exception as exc:
            print(f"[db] WARNING: Supabase reachable-check failed: {exc}")

    def save_document(self, doc: Dict[str, Any]) -> None:
        self.client.table("documents").insert({c: doc[c] for c in DOCUMENT_COLUMNS}).execute()

    def get_all_documents(self) -> List[Dict[str, Any]]:
        res = self.client.table("documents").select("*").order("created_at", desc=True).execute()
        return res.data or []

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        res = (
            self.client.table("documents")
            .select("*")
            .eq("document_id", document_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def delete_document(self, document_id: str) -> None:
        self.client.table("documents").delete().eq("document_id", document_id).execute()

    def save_message(
        self,
        conversation_id: str,
        message_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: str = "",
    ) -> None:
        created_at = created_at or datetime.now(timezone.utc).isoformat()
        # Ensure the parent conversation exists (mirrors SQLite INSERT OR IGNORE)
        existing = (
            self.client.table("conversations")
            .select("conversation_id")
            .eq("conversation_id", conversation_id)
            .limit(1)
            .execute()
        )
        if not existing.data:
            self.client.table("conversations").insert({
                "conversation_id": conversation_id,
                "created_at": created_at,
            }).execute()
        row = {
            "message_id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": created_at,
        }
        if metadata is not None:
            row["metadata"] = metadata  # dict → jsonb
        self.client.table("messages").insert(row).execute()

    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        res = (
            self.client.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at")
            .execute()
        )
        rows = res.data or []
        for d in rows:
            # jsonb already arrives as dict; keep str-tolerant for safety
            if isinstance(d.get("metadata"), str):
                try:
                    d["metadata"] = json.loads(d["metadata"])
                except Exception:
                    pass
        return rows

    # --- Conversation history (chat history panel) ---

    def save_conversation(
        self,
        conversation_id: str,
        created_at: str,
        title: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        updated_at = updated_at or created_at
        payload = {
            "conversation_id": conversation_id,
            "created_at": created_at,
            "updated_at": updated_at,
        }
        if title is not None:
            payload["title"] = title
        self.client.table("conversations").upsert(
            payload, on_conflict="conversation_id"
        ).execute()

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        res = (
            self.client.table("conversations")
            .select("*")
            .eq("conversation_id", conversation_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        return rows[0] if rows else None

    def list_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        res = (
            self.client.table("conversations")
            .select("conversation_id, title, created_at, updated_at")
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        results = []
        for d in (res.data or []):
            d["title"] = d.get("title") or "New conversation"
            d["updated_at"] = d.get("updated_at") or d.get("created_at")
            results.append(d)
        return results

    def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        payload: Dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if updated_at is not None:
            payload["updated_at"] = updated_at
        if not payload:
            return
        self.client.table("conversations").update(payload).eq(
            "conversation_id", conversation_id
        ).execute()

    def delete_conversation(self, conversation_id: str) -> None:
        self.client.table("messages").delete().eq(
            "conversation_id", conversation_id
        ).execute()
        self.client.table("conversations").delete().eq(
            "conversation_id", conversation_id
        ).execute()

    def count_all_stats(self) -> Dict[str, int]:
        docs = (
            self.client.table("documents")
            .select("chunk_count", count=self._count_exact())
            .execute()
        )
        convs = (
            self.client.table("conversations")
            .select("conversation_id", count=self._count_exact())
            .execute()
        )
        chunk_total = sum((r.get("chunk_count") or 0) for r in (docs.data or []))
        doc_count = docs.count if docs.count is not None else len(docs.data or [])
        conv_count = convs.count if convs.count is not None else len(convs.data or [])
        return {
            "documents": doc_count,
            "chunks": chunk_total,
            "conversations": conv_count,
        }


# --------------------------------------------------------------------------- #
# Active backend + public API (unchanged signatures — call sites don't change)
# --------------------------------------------------------------------------- #

BACKEND = SupabaseBackend() if (SUPABASE_URL and SUPABASE_ANON_KEY) else SqliteBackend()


def init_db() -> None:
    print(f"[db] active backend: {BACKEND.name} ({BACKEND.description})")
    BACKEND.init_db()


def save_document(doc: Dict[str, Any]) -> None:
    BACKEND.save_document(doc)


def get_all_documents() -> List[Dict[str, Any]]:
    return BACKEND.get_all_documents()


def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    return BACKEND.get_document_by_id(document_id)


def delete_document(document_id: str) -> None:
    BACKEND.delete_document(document_id)


def save_message(
    conversation_id: str,
    message_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    created_at: str = "",
) -> None:
    BACKEND.save_message(
        conversation_id=conversation_id,
        message_id=message_id,
        role=role,
        content=content,
        metadata=metadata,
        created_at=created_at,
    )


def get_conversation_messages(conversation_id: str) -> List[Dict[str, Any]]:
    return BACKEND.get_conversation_messages(conversation_id)


def save_conversation(
    conversation_id: str,
    created_at: str,
    title: Optional[str] = None,
    updated_at: Optional[str] = None,
) -> None:
    BACKEND.save_conversation(
        conversation_id=conversation_id,
        created_at=created_at,
        title=title,
        updated_at=updated_at,
    )


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    return BACKEND.get_conversation(conversation_id)


def list_conversations(limit: int = 100) -> List[Dict[str, Any]]:
    return BACKEND.list_conversations(limit)


def update_conversation(
    conversation_id: str,
    title: Optional[str] = None,
    updated_at: Optional[str] = None,
) -> None:
    BACKEND.update_conversation(
        conversation_id=conversation_id, title=title, updated_at=updated_at
    )


def delete_conversation(conversation_id: str) -> None:
    BACKEND.delete_conversation(conversation_id)


def count_all_stats() -> Dict[str, int]:
    return BACKEND.count_all_stats()



