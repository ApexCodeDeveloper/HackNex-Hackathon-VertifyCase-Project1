import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { DocumentMetadata, EvidenceChunk, HealthResponse } from "./types";
import OverviewPage from "./OverviewPage";
import DocumentsPage from "./DocumentsPage";
import ResearchPage from "./ResearchPage";
import CaseReviewPage from "./CaseReviewPage";
import ContradictionsPage from "./ContradictionsPage";
import EvidencePanel from "./EvidencePanel";

type PageKey = "overview" | "documents" | "research" | "case-review" | "contradictions";

const NAV: { key: PageKey; label: string; hint: string }[] = [
  { key: "overview", label: "Overview", hint: "System status & quick start" },
  { key: "documents", label: "Documents", hint: "Upload & manage PDFs" },
  { key: "research", label: "Research", hint: "Grounded chat with citations" },
  { key: "case-review", label: "Case Review", hint: "Multi-document synthesis" },
  { key: "contradictions", label: "Contradictions", hint: "Cross-document conflicts" },
];

export default function App() {
  const [page, setPage] = useState<PageKey>("overview");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [evidenceChunk, setEvidenceChunk] = useState<EvidenceChunk | null>(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);

  const refreshDocuments = useCallback(() => {
    api.listDocuments().then(setDocuments).catch(() => setDocuments([]));
  }, []);

  const refreshHealth = useCallback(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    refreshDocuments();
    refreshHealth();
    const id = window.setInterval(refreshHealth, 30000);
    return () => window.clearInterval(id);
  }, [refreshDocuments, refreshHealth]);

  const openEvidence = useCallback(async (chunkId: string) => {
    setEvidenceLoading(true);
    setEvidenceError(null);
    setEvidenceChunk(null);
    try {
      const chunk = await api.getEvidence(chunkId);
      setEvidenceChunk(chunk);
    } catch (e) {
      setEvidenceError(e instanceof Error ? e.message : "Failed to load evidence.");
    } finally {
      setEvidenceLoading(false);
    }
  }, []);

  const closeEvidence = useCallback(() => {
    setEvidenceChunk(null);
    setEvidenceError(null);
  }, []);

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <aside className="flex w-64 shrink-0 flex-col border-r border-slate-800 bg-slate-900/60">
        <div className="border-b border-slate-800 px-5 py-5">
          <div className="text-sm font-semibold tracking-[0.12em] text-amber-400">
            VertifyCase
          </div>
          <div className="mt-1 text-sm font-medium text-slate-200">
            Grounded Legal Assistant
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Every claim verified against source evidence
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV.map((item) => {
            const active = page === item.key;
            return (
              <button
                key={item.key}
                onClick={() => setPage(item.key)}
                className={`w-full rounded-md px-3 py-2.5 text-left transition ${
                  active
                    ? "bg-amber-500/10 text-amber-300 ring-1 ring-amber-500/30"
                    : "text-slate-300 hover:bg-slate-800 hover:text-slate-100"
                }`}
              >
                <div className="text-sm font-medium">{item.label}</div>
                <div className="text-xs text-slate-500">{item.hint}</div>
              </button>
            );
          })}
        </nav>

        <div className="border-t border-slate-800 px-5 py-4 text-xs">
          {health ? (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Backend</span>
                <span className={health.status === "ok" ? "text-emerald-400" : "text-rose-400"}>
                  {health.status === "ok" ? "Connected" : health.status}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">ChromaDB</span>
                <span className={health.chroma_ready ? "text-emerald-400" : "text-rose-400"}>
                  {health.chroma_ready ? "Ready" : "Offline"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Gemini</span>
                <span className={health.gemini_configured ? "text-emerald-400" : "text-amber-400"}>
                  {health.gemini_configured ? "Configured" : "Not configured"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Indexed</span>
                <span className="text-slate-300">{health.indexed_documents} docs</span>
              </div>
            </div>
          ) : (
            <div className="text-rose-400">Backend unreachable</div>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="thin-scroll relative flex-1 overflow-y-auto">
        {page === "overview" && (
          <OverviewPage
            health={health}
            documents={documents}
            onNavigate={setPage}
            onRefresh={() => {
              refreshDocuments();
              refreshHealth();
            }}
          />
        )}
        {page === "documents" && (
          <DocumentsPage
            documents={documents}
            onChanged={() => {
              refreshDocuments();
              refreshHealth();
            }}
          />
        )}
        {page === "research" && <ResearchPage onOpenEvidence={openEvidence} documents={documents} />}
        {page === "case-review" && (
          <CaseReviewPage documents={documents} onOpenEvidence={openEvidence} />
        )}
        {page === "contradictions" && (
          <ContradictionsPage documents={documents} onOpenEvidence={openEvidence} />
        )}

        {/* Evidence slide-over */}
        {(evidenceChunk || evidenceLoading || evidenceError) && (
          <EvidencePanel
            chunk={evidenceChunk}
            loading={evidenceLoading}
            error={evidenceError}
            onClose={closeEvidence}
          />
        )}
      </main>
    </div>
  );
}

