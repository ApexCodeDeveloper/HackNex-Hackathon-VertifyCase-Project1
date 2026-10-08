import { useState } from "react";
import { api } from "./api";
import type { ContradictionsResponse, DocumentMetadata } from "./types";

interface Props {
  documents: DocumentMetadata[];
  onOpenEvidence: (chunkId: string) => void;
}

export default function ContradictionsPage({ documents, onOpenEvidence }: Props) {
  const [selected, setSelected] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ContradictionsResponse | null>(null);

  const toggle = (id: string) =>
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );

  const run = async () => {
    if (running) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.analyzeContradictions(selected);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-8 py-10">
      <h1 className="text-2xl font-semibold text-slate-100">Contradictions</h1>
      <p className="mt-1 text-sm text-slate-400">
        Compare documents and surface factual discrepancies between them — e.g. an original clause
        versus an amendment. Empty selection scans all indexed documents.
      </p>

      <div className="mt-6 rounded-lg border border-slate-800 bg-slate-900/50 p-4">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Documents to compare
        </div>
        {documents.length === 0 ? (
          <div className="mt-3 text-sm text-slate-500">
            No documents uploaded yet — add PDFs in the Documents tab first.
          </div>
        ) : (
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              onClick={() => setSelected([])}
              className={`rounded-md px-3 py-1.5 text-sm ring-1 transition ${
                selected.length === 0
                  ? "bg-amber-500/15 text-amber-300 ring-amber-500/40"
                  : "text-slate-400 ring-slate-700 hover:bg-slate-800"
              }`}
            >
              All documents
            </button>
            {documents.map((d) => {
              const active = selected.includes(d.document_id);
              return (
                <button
                  key={d.document_id}
                  onClick={() => toggle(d.document_id)}
                  className={`rounded-md px-3 py-1.5 text-sm ring-1 transition ${
                    active
                      ? "bg-amber-500/15 text-amber-300 ring-amber-500/40"
                      : "text-slate-400 ring-slate-700 hover:bg-slate-800"
                  }`}
                >
                  {active ? "✓ " : ""}
                  {d.document_name}
                </button>
              );
            })}
          </div>
        )}
        <button
          onClick={() => void run()}
          disabled={running || documents.length === 0}
          className="mt-4 rounded-md bg-amber-500 px-5 py-2 text-sm font-medium text-slate-950 hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {running ? "Comparing documents…" : "Analyze for contradictions"}
        </button>
      </div>

      {error && (
        <div className="mt-4 rounded-md border border-rose-700 bg-rose-950/40 p-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Findings
          </h2>
          {result.message && (
            <div className="mt-2 rounded-md border border-slate-700 bg-slate-900 p-3 text-sm text-slate-400">
              {result.message}
            </div>
          )}
          {result.contradictions.length === 0 && !result.message && (
            <div className="mt-3 rounded-md border border-emerald-800 bg-emerald-950/30 p-4 text-sm text-emerald-300">
              No contradictions supported by the evidence across the selected documents.
            </div>
          )}
          <div className="mt-3 space-y-4">
            {result.contradictions.map((c, i) => (
              <div key={i} className="rounded-lg border border-rose-800/60 bg-rose-950/20 p-5">
                <div className="text-sm font-medium text-rose-300">{c.topic}</div>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  {[c.claim_a, c.claim_b].map((claim, j) => (
                    <div
                      key={j}
                      className="rounded border border-slate-700 bg-slate-950/60 p-3"
                    >
                      <div className="flex items-center justify-between text-[11px] uppercase tracking-wider text-slate-500">
                        <span>
                          {claim.source ?? (j === 0 ? "Source A" : "Source B")}
                          {claim.page != null ? ` p.${claim.page}` : ""}
                        </span>
                        {claim.chunk_id && (
                          <button
                            onClick={() => onOpenEvidence(claim.chunk_id!)}
                            className="text-amber-300 hover:text-amber-200"
                          >
                            view source →
                          </button>
                        )}
                      </div>
                      <p className="mt-1.5 text-sm text-slate-300">{claim.text ?? ""}</p>
                    </div>
                  ))}
                </div>
                <p className="mt-3 text-xs leading-relaxed text-slate-400">{c.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
