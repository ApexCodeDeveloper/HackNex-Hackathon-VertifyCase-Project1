# VertifyCase — Grounded Agentic Legal Assistant

> HackNex project ID: **HNX26EPS01** · Website name: **VertifyCase**

A retrieval-augmented legal document intelligence workstation: upload real PDFs, ask questions,
run multi-document case reviews and contradiction analyses. Every factual claim in an answer is
verified against retrieved source chunks before it is shown — unsupported claims are stripped, and
when no evidence verifies the response the system clamps to an explicit
**“Insufficient evidence in the provided documents.”** Nothing is fabricated, no data is pre-seeded.

**Stack:** FastAPI · ChromaDB · SQLite · Gemini (`google-genai`) · React + TypeScript + Vite + Tailwind CSS

---

## Run the backend

```powershell
cd d:\HackNex\backend
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

Backend config lives in `backend/.env` (see `backend/.env.example`):

| Variable         | Purpose                                        | Default                     |
| ---------------- | ---------------------------------------------- | --------------------------- |
| `GEMINI_API_KEY` | Required for chat / case review / contradictions | *(empty → honest error state)* |
| `GEMINI_MODEL`   | Gemini model used for grounded reasoning       | `gemini-flash-lite-latest`  |
| `TOP_K`          | Retrieval depth per query                      | `10`                        |
| `CORS_ORIGINS`   | Allowed origins (JSON array)                   | Vite on `localhost:5173`    |
| `SUPABASE_URL`   | Supabase project URL — **set both** to use hosted Postgres | *(empty → local SQLite)* |
| `SUPABASE_ANON_KEY` | Supabase anon API key                       | *(empty → local SQLite)*    |

### Database backends (SQLite ↔ Supabase)

The backend picks its database automatically from `backend/.env`:

- **Both `SUPABASE_*` vars empty** → local **SQLite** (`database/legal_assistant.db`) — the default.
- **Both set** → **Supabase** (hosted PostgreSQL) via `supabase-py`. Same API, no other code changes.

To switch to Supabase:

1. Create a free project at <https://supabase.com>.
2. Open **SQL Editor → New query**, paste the whole of `backend/supabase_schema.sql`, press **Run**
   (creates `documents`, `conversations`, `messages` + indexes + RLS policies; idempotent).
3. **Settings → API** → copy the *Project URL* and *anon public* key into `backend/.env`:

   ```ini
   SUPABASE_URL=https://<project-ref>.supabase.co
   SUPABASE_ANON_KEY=<anon key>
   ```

4. *(Optional, keeps your existing rows)* migrate local SQLite data:

   ```powershell
   cd d:\HackNex\backend
   python migrate_sqlite_to_supabase.py
   ```

5. Restart the backend — `/api/health` now reports `"db_backend": "supabase"`.

> **Unchanged by the swap:** vector embeddings stay in Chroma (`data/chroma/`), uploaded PDFs stay in
> `data/documents/`, and Gemini reasoning is unaffected. For a full cloud deploy, point `CHROMA_PATH`
> at a persistent disk or migrate Chroma to a hosted store (e.g. Chroma Cloud / pgvector).

Health check: <http://127.0.0.1:8000/api/health>

> **Note on the Gemini free tier:** quotas are per model and per day (~20 requests/day for some
> models). If you get `429 RESOURCE_EXHAUSTED`, either wait for the quota to reset or switch
> `GEMINI_MODEL` in `backend/.env` to another model your key can use (e.g.
> `gemini-flash-latest`), then restart the backend. 503 load spikes are retried automatically
> with backoff; 429 quota errors are not (retrying would only waste quota).

## Run the frontend

```powershell
cd d:\HackNex\frontend
npm install
npm run dev
```

Open **<http://localhost:5173>**. The Vite dev server proxies `/api` and `/files` to the backend
on port 8000, so no CORS issues occur in development.

Production build:

```powershell
cd d:\HackNex\frontend
npm run build        # outputs to frontend/dist
```

## API surface

| Method | Path                        | Purpose                                             |
| ------ | --------------------------- | --------------------------------------------------- |
| GET    | `/api/health`               | Backend, ChromaDB, Gemini status                    |
| GET    | `/api/stats`                | Document / chunk / conversation counts              |
| POST   | `/api/documents/upload`     | Upload a PDF (multipart `file`), indexes it         |
| GET    | `/api/documents`            | List indexed documents                              |
| DELETE | `/api/documents/{id}`       | Delete document + its chunks + stored file          |
| POST   | `/api/chat`                 | `{message, conversation_id?, document_ids?}` → grounded answer with verified claims |
| GET    | `/api/conversations/{id}`   | Conversation history                                |
| GET    | `/api/evidence/{chunk_id}`  | Verbatim source chunk behind a citation             |
| POST   | `/api/analyze/contradictions` | `{document_ids: []}` (empty = all docs) → contradictions |
| POST   | `/api/analyze/case-review`  | `{document_ids: [...]}` → summary, key facts, contradictions, missing info |

## How grounding is enforced

1. **Retrieval first** — ChromaDB returns the top-k chunks for the question (optionally scoped to
   selected documents).
2. **Grounded generation** — Gemini answers strictly from the supplied evidence in JSON form:
   claims must reference real chunk IDs, or state insufficient evidence.
3. **Verification** (`verification.py`) — claims whose `source_ids` don't map to actually
   retrieved chunks are stripped; if nothing verifies, the answer is clamped to the
   insufficient-evidence statement; confidence is derived from what survived, not from the model.
4. **Citation UI** — every claim shows its source chips; clicking one fetches
   `/api/evidence/{chunk_id}` so the user reads the verbatim extracted text, page number and
   relevance score.

## App pages

- **Overview** — system health (backend / ChromaDB / Gemini), workspace stats, workflow guide
- **Documents** — drag-and-drop PDF upload, index status, delete (with rollback on indexing failure)
- **Research** — grounded chat with per-claim citations, confidence badges, missing-info panel,
  document scoping, and a slide-over evidence viewer
- **Case Review** — multi-document synthesis: summary, evidence-backed key facts, contradictions,
  missing information, confidence
- **Contradictions** — cross-document conflict detection (e.g. original clause vs. amendment)

## Repository layout

```
backend/    FastAPI app (config, models, database, documents, rag, reasoning, verification, main)
frontend/   React + Vite + Tailwind app (src/, public/)
data/       Runtime: uploaded PDFs + Chroma index (git-ignored)
database/   SQLite file (git-ignored)
```
