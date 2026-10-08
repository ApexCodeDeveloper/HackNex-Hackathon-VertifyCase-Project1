import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from config import DATABASE_PATH

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Documents table
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
    
    # Conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        )
    """)
    
    # Messages table
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
    
    conn.commit()
    conn.close()

def save_document(doc: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO documents (document_id, document_name, file_path, file_size, page_count, chunk_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        doc["document_id"],
        doc["document_name"],
        doc["file_path"],
        doc["file_size"],
        doc["page_count"],
        doc["chunk_count"],
        doc["created_at"]
    ))
    conn.commit()
    conn.close()

def get_all_documents() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def delete_document(document_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
    conn.commit()
    conn.close()

def save_message(conversation_id: str, message_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None, created_at: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO conversations (conversation_id, created_at) VALUES (?, ?)", (conversation_id, created_at))
    cursor.execute("""
        INSERT INTO messages (message_id, conversation_id, role, content, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        message_id,
        conversation_id,
        role,
        content,
        json.dumps(metadata) if metadata else None,
        created_at
    ))
    conn.commit()
    conn.close()

def get_conversation_messages(conversation_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        if d.get("metadata"):
            try:
                d["metadata"] = json.loads(d["metadata"])
            except Exception:
                pass
        results.append(d)
    return results

def count_all_stats() -> Dict[str, int]:
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
        "conversations": conv_count
    }
