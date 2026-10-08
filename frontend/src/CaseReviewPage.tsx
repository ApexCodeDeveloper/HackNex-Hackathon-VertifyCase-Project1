import { useState } from "react";
import { api } from "./api";
import type { CaseReviewResponse, DocumentMetadata, GroundedClaim } from "./types";

interface Props {
  documents: DocumentMetadata[];
  onOpenEvidence: (chunkId: string) => void;
}

export default function CaseReviewPage({ documents, onOpenEvidence }: Props) {
  const [selected, setSelected] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CaseReviewResponse | null>(null);

  const toggle = (id: string) =>
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );

  const run = async () => {
    if (selected.length === 0 || running) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.caseReview(selected);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Case review failed.");
    } finally {
      setRunning(false);
    }
  };

  const docName = (id: string) =>
    documents.find((d) => d.document_id === id)?.document_name ?? id;

  return (
    <div className="mx-auto max-w-5xl px-8 py-10">
      <h1 className="text-2xl font-semibold text-slate-100">Case Review</h1>
      <p className="mt-1 text-sm text-slate-400">
        Select documents to synthesize. The assistant extracts key facts with citations, flags
        contradictions, lists what the evidence does not cover, and states a confidence level.
      </p>

      {/* Document selection */}
      <div className="mt-6 rounded-lg border border-slate-800 bg-slate-900/50 p-4">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Documents to review
        </div>
        {documents.length === 0 ? (
          <div className="mt-3 text-sm text-slate-500">
            No documents uploaded yet — add PDFs in the Documents tab first.
          </div>
        ) : (
          <div className="mt-3 flex flex-wrap gap-2">
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
          disabled={selected.length === 0 || running}
          className="mt-4 rounded-md bg-amber-500 px-5 py-2 text-sm font-medium text-slate-950 hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {running ? "Reviewing evidence…" : `Run case review (${selected.length} selected)`}
        </button>
      </div>

      {error && (
        <div className="mt-4 rounded-md border border-rose-700 bg-rose-950/40 p-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      {result && (
        <CaseReviewResult
          result={result}
          docName={docName}
          onOpenEvidence={onOpenEvidence}
        />
      )}
    </div>
  );
}

function CaseReviewResult({
  result,
  docName,
  onOpenEvidence,
}: {
  result: CaseReviewResponse;
  docName: (id: string) => string;
  onOpenEvidence: (chunkId: string) => void;
}) {
  const confCls =
    result.confidence === "high"
      ? "text-emerald-400"
      : result.confidence === "medium"
        ? "text-amber-400"
        : "text-rose-400";

  return (
    <div className="mt-8 space-y-6">
      {/* Summary */}
      <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Summary — {result.document_names.join(", ")}
          </h2>
          <span className={`text-xs uppercase tracking-wider ${confCls}`}>
            {result.confidence} confidence
          </span>
        </div>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-200">
          {result.summary}
        </p>
      </section>

      {/* Key facts */}
      <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Key facts (evidence-backed)
        </h2>
        {result.key_facts.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">
            No facts could be verified against the evidence.
          </p>
        ) : (
          <ul className="mt-3 space-y-2">
            {result.key_facts.map((f: GroundedClaim, i: number) => (
              <li key={i} className="text-sm text-slate-300">
                <span className="mr-1 text-emerald-400">✓</span>
                {f.claim}{" "}
                {f.source_ids.map((id, j) => (
                  <button
                    key={id}
                    onClick={() => onOpenEvidence(id)}
                    className={`rounded bg-slate-800 px-1.5 py-0.5 text-[11px] text-amber-300 ring-1 ring-slate-700 hover:bg-slate-700 ${j > 0 ? "ml-1" : "ml-1"}`}
                    title={`Open source evidence: ${id}`}
                  >
                    {id}
                  </button>
                ))}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Contradictions */}
      <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Contradictions found
        </h2>
        {result.contradictions.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">
            No contradictions supported by the evidence.
          </p>
        ) : (
          <div className="mt-3 space-y-3">
            {result.contradictions.map((c, i) => (
              <div key={i} className="rounded-md border border-rose-800/60 bg-rose-950/20 p-4">
                <div className="text-sm font-medium text-rose-300">{c.topic}</div>
                <div className="mt-2 grid gap-2 md:grid-cols-2">
                  <ClaimBox
                    label={c.claim_a.source ?? "Source A"}
                    page={c.claim_a.page}
                    text={c.claim_a.text ?? ""}
                    chunkId={c.claim_a.chunk_id}
                    onOpenEvidence={onOpenEvidence}
                  />
                  <ClaimBox
                    label={c.claim_b.source ?? "Source B"}
                    page={c.claim_b.page}
                    text={c.claim_b.text ?? ""}
                    chunkId={c.claim_b.chunk_id}
                    onOpenEvidence={onOpenEvidence}
                  />
                </div>
                <p className="mt-2 text-xs leading-relaxed text-slate-400">{c.explanation}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Missing information */}
      <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Missing from the evidence
        </h2>
        {result.missing_information.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">Nothing flagged.</p>
        ) : (
          <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-amber-200/90">
            {result.missing_information.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function ClaimBox({
  label,
  page,
  text,
  chunkId,
  onOpenEvidence,
}: {
  label: string;
  page?: number;
  text: string;
  chunkId?: string;
  onOpenEvidence: (chunkId: string) => void;
}) {
  return (
    <div className="rounded border border-slate-700 bg-slate-950/60 p-3">
      <div className="flex items-center justify-between text-[11px] uppercase tracking-wider text-slate-500">
        <span>
          {label}
          {page != null ? ` p.${page}` : ""}
        </span>
        {chunkId && (
          <button
            onClick={() => onOpenEvidence(chunkId)}
            className="text-amber-300 hover:text-amber-200"
          >
            view source →
          </button>
        )}
      </div>
      <p className="mt-1.5 text-sm text-slate-300">{text}</p>
    </div>
  );
}
