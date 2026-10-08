import type { DocumentMetadata, HealthResponse } from "./types";

interface Props {
  health: HealthResponse | null;
  documents: DocumentMetadata[];
  onNavigate: (page: "documents" | "research" | "case-review" | "contradictions") => void;
  onRefresh: () => void;
}

const STEPS = [
  {
    title: "1. Upload documents",
    body: "Add real PDFs — contracts, case files, pleadings. Pages are extracted and chunked with exact page provenance, then embedded into ChromaDB.",
    action: "Go to Documents" as const,
    page: "documents" as const,
  },
  {
    title: "2. Ask legal questions",
    body: "Every answer is grounded: claims without verified source citations are stripped, and with no verified evidence the system clamps to an explicit insufficient-evidence statement.",
    action: "Open Research" as const,
    page: "research" as const,
  },
  {
    title: "3. Inspect the evidence",
    body: "Click any citation marker to open the source panel and read the verbatim extracted text, page number, and retrieval relevance score.",
    action: "Open Research" as const,
    page: "research" as const,
  },
  {
    title: "4. Review & compare",
    body: "Run multi-document case review or contradiction analysis across uploaded files. Findings are tied back to exact chunk IDs — nothing is invented.",
    action: "Open Case Review" as const,
    page: "case-review" as const,
  },
];

export default function OverviewPage({ health, documents, onNavigate, onRefresh }: Props) {
  const totalChunks = documents.reduce((sum, d) => sum + d.chunk_count, 0);

  return (
    <div className="mx-auto max-w-5xl px-8 py-10">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Overview</h1>
          <p className="mt-1 text-sm text-slate-400">
            Agentic legal document intelligence — retrieval-augmented, citation-verified, zero
            fabricated data.
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800"
        >
          Refresh status
        </button>
      </div>

      {/* Stat cards */}
      <div className="mt-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Documents" value={String(documents.length)} />
        <StatCard label="Indexed chunks" value={String(totalChunks)} />
        <StatCard
          label="ChromaDB"
          value={health ? (health.chroma_ready ? "Ready" : "Offline") : "—"}
          tone={health?.chroma_ready ? "good" : "bad"}
        />
        <StatCard
          label="Gemini"
          value={health ? (health.gemini_configured ? "Configured" : "Missing key") : "—"}
          tone={health?.gemini_configured ? "good" : "warn"}
        />
      </div>

      {!health?.gemini_configured && (
        <div className="mt-6 rounded-md border border-amber-700/60 bg-amber-950/30 p-4 text-sm text-amber-200">
          <strong className="font-semibold">GEMINI_API_KEY not set.</strong> Chat and analysis will
          return an honest “AI analysis unavailable” response until you add the key to{" "}
          <code className="rounded bg-slate-900 px-1 py-0.5 text-xs">backend/.env</code> and restart
          the backend.
        </div>
      )}

      {/* Workflow */}
      <div className="mt-10">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          How this workstation works
        </h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {STEPS.map((s) => (
            <div key={s.title} className="rounded-lg border border-slate-800 bg-slate-900/50 p-5">
              <div className="font-medium text-slate-100">{s.title}</div>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{s.body}</p>
              <button
                onClick={() => onNavigate(s.page)}
                className="mt-3 text-sm font-medium text-amber-400 hover:text-amber-300"
              >
                {s.action} →
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Recent documents */}
      <div className="mt-10">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Documents in workspace
          </h2>
          <button
            onClick={() => onNavigate("documents")}
            className="text-sm text-amber-400 hover:text-amber-300"
          >
            Manage →
          </button>
        </div>
        {documents.length === 0 ? (
          <div className="mt-4 rounded-lg border border-dashed border-slate-700 p-8 text-center text-sm text-slate-500">
            No documents yet. Upload a PDF to begin — the app starts empty by design.
          </div>
        ) : (
          <ul className="mt-4 divide-y divide-slate-800 rounded-lg border border-slate-800">
            {documents.slice(0, 5).map((d) => (
              <li key={d.document_id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <div className="text-sm text-slate-200">{d.document_name}</div>
                  <div className="text-xs text-slate-500">
                    {d.page_count} page{d.page_count === 1 ? "" : "s"} · {d.chunk_count} chunks
                  </div>
                </div>
                <div className="text-xs text-slate-500">
                  {new Date(d.created_at).toLocaleString()}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "good" | "warn" | "bad";
}) {
  const toneClass =
    tone === "good"
      ? "text-emerald-400"
      : tone === "warn"
        ? "text-amber-400"
        : tone === "bad"
          ? "text-rose-400"
          : "text-slate-100";
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
      <div className="text-xs uppercase tracking-wider text-slate-500">{label}</div>
      <div className={`mt-1 text-xl font-semibold ${toneClass}`}>{value}</div>
    </div>
  );
}

