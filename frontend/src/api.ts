import type {
  CaseReviewResponse,
  ChatResponse,
  ContradictionsResponse,
  ConversationResponse,
  DocumentMetadata,
  EvidenceChunk,
  HealthResponse,
  StatsResponse,
} from "./types";

// Same-origin calls: Vite dev server proxies /api and /files to FastAPI :8000.
// For a production build serving the frontend from FastAPI, this stays valid too.
const BASE = "";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (Array.isArray(body?.detail)) detail = body.detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join("; ");
      else if (body?.detail) detail = JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: (): Promise<HealthResponse> =>
    fetch(`${BASE}/api/health`).then(handle<HealthResponse>),

  stats: (): Promise<StatsResponse> =>
    fetch(`${BASE}/api/stats`).then(handle<StatsResponse>),

  uploadDocument: (file: File): Promise<DocumentMetadata> => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/api/documents/upload`, { method: "POST", body: form }).then(
      handle<DocumentMetadata>
    );
  },

  listDocuments: (): Promise<DocumentMetadata[]> =>
    fetch(`${BASE}/api/documents`).then(handle<DocumentMetadata[]>),

  deleteDocument: (id: string): Promise<{ status: string; message: string }> =>
    fetch(`${BASE}/api/documents/${id}`, { method: "DELETE" }).then(
      handle<{ status: string; message: string }>
    ),

  chat: (body: {
    message: string;
    conversation_id?: string | null;
    document_ids?: string[] | null;
  }): Promise<ChatResponse> =>
    fetch(`${BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(handle<ChatResponse>),

  getConversation: (id: string): Promise<ConversationResponse> =>
    fetch(`${BASE}/api/conversations/${id}`).then(handle<ConversationResponse>),

  getEvidence: (chunkId: string): Promise<EvidenceChunk> =>
    fetch(`${BASE}/api/evidence/${encodeURIComponent(chunkId)}`).then(
      handle<EvidenceChunk>
    ),

  analyzeContradictions: (document_ids: string[]): Promise<ContradictionsResponse> =>
    fetch(`${BASE}/api/analyze/contradictions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_ids }),
    }).then(handle<ContradictionsResponse>),

  caseReview: (document_ids: string[]): Promise<CaseReviewResponse> =>
    fetch(`${BASE}/api/analyze/case-review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_ids }),
    }).then(handle<CaseReviewResponse>),
};
