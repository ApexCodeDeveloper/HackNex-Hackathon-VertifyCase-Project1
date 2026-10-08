import os
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")

PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

CHROMA_PATH = os.getenv("CHROMA_PATH", str(ROOT_DIR / "data" / "chroma"))
DATABASE_PATH = os.getenv("DATABASE_PATH", str(ROOT_DIR / "database" / "legal_assistant.db"))
STORAGE_PATH = os.getenv("STORAGE_PATH", str(ROOT_DIR / "data" / "documents"))

# Supabase (hosted PostgreSQL) — set both to activate the Supabase backend;
# leave empty to keep using local SQLite. Tables: supabase_schema.sql
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()

# Ensure paths exist
Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
Path(STORAGE_PATH).mkdir(parents=True, exist_ok=True)

raw_cors = os.getenv("CORS_ORIGINS", '["http://localhost:5173","http://127.0.0.1:5173"]')
try:
    CORS_ORIGINS = json.loads(raw_cors)
except Exception:
    CORS_ORIGINS = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

TOP_K = int(os.getenv("TOP_K", "10"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
