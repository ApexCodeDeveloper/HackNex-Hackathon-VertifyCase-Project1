import { useMemo, useState } from "react";
import { api } from "./api";
import type { DraftDocType, DraftResponse, DocumentMetadata } from "./types";

interface Props {
  documents: DocumentMetadata[];
  onOpenEvidence: (chunkId: string) => void;
}

const DOC_TYPES: { key: DraftDocType; label: string; hint: string }[] = [
  { key: "motion", label: "Motion", hint: "Caption, facts, argument, prayer for relief" },
  { key: "memorandum", label: "Legal Memo", hint: "Question, answer, facts, analysis" },
  { key: "demand_letter", label: "Demand Letter", hint: "Re line, matter, demand, deadline" },
  { key: "contract_clause", label: "Contract Clause", hint: "Operative language, conditions, remedies" },
  { key: "general", label: "General Draft", hint: "Any structured legal document" },
];

export default function DraftingPage({ documents, onOpenEvidence }: Props) {
  const [selected, setSelected] = useState<string[]>([]);
  const [docType, setDocType] = useState<DraftDocType>("motion");
  const [instructions, setInstructions] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DraftResponse | null>(null);
  const [draftBody, setDraftBody] = useState("");
  const [copied, setCopied] = useState(false);

  const toggle = (id: string) =>
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );

  const sourcesById = useMemo(() => {
    const map = new Map<string, { name: string; page: number }>();
    if (result) {
      for (const s of result.sources) {
        map.set(s.chunk_id, { name: s.document_name, page: s.page_number });
      }
    }
    return map;
  }, [result]);

  const run = async () => {
    if (instructions.trim() === "" || running) return;
    setRunning(true);
    setError(null);
    setResult(null);
    setCopied(false);
    try {
      const res = await api.draft({
        document_ids: selected,
        doc_type: docType,
        instructions: instructions.trim(),
      });
      setResult(res);
      setDraftBody(res.draft_text);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Drafting failed.");
    } finally {
      setRunning(false);
    }
  };

  const copyDraft = async () => {
    try {
      await navigator.clipboard.writeText(draftBody);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  };

  const downloadDraft = () => {
    const blob = new Blob([draftBody], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `draft-${docType}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="mx-auto max-w-5xl px-8 py-10">
      <h1 className="text-2xl font-semibold text-slate-100">Legal Drafting</h1>
      <p className="mt-1 text-sm text-slate-400">
        Draft a legal document grounded strictly in your uploaded evidence. Every factual
        statement is traced to a source chunk - unsupported claims are stripped, and gaps are
        flagged instead of invented.
      </p>

      {/* Document type */}
      <div className="mt-6 rounded-lg border border-slate-800 bg-slate-900/50 p-4">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Document type
        </div>
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {DOC_TYPES.map((t) => {
            const active = docType === t.key;
            return (
              <button
                key={t.key}
                onClick={() => setDocType(t.key)}
                className={`rounded-md px-3 py-2 text-left text-sm ring-1 transition ${
                  active
                    ? "bg-amber-500/15 text-amber-300 ring-amber-500/40"
                    : "text-slate-300 ring-slate-700 hover:bg-slate-800"
                }`}
              >
                <div className="font-medium">{t.label}</div>
                <div className="text-xs text-slate-500">{t.hint}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/50 p-4">
        <label
          htmlFor="draft-instructions"
          className="text-xs font-semibold uppercase tracking-wider text-slate-500"
        >
          Drafting instructions
        </label>
        <textarea
          id="draft-instructions"
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          rows={3}
          placeholder="e.g. Draft a motion to compel production of the survey records described in the case file."
          className="mt-2 w-full resize-y rounded-md border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:border-amber-500/60 focus:outline-none"
        />
      </div>

      {/* Document selection */}
      <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/50 p-4">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Source documents{" "}
          <span className="font-normal normal-case text-slate-600">
            (none selected = use all)
          </span>
        </div>
        {documents.length === 0 ? (
          <div className="mt-3 text-sm text-slate-500">
            No documents uploaded yet - add PDFs in the Documents tab first.
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
                  {active ? "OK " : ""}
                  {d.document_name}
                </button>
              );
            })}
          </div>
        )}
        <button
          onClick={() => void run()}
          disabled={instructions.trim() === "" || running || documents.length === 0}
          className="mt-4 rounded-md bg-amber-500 px-5 py-2 text-sm font-medium text-slate-950 hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {running ? "Drafting..." : "Generate draft"}
        </button>
      </div>

      {error && (
        <div className="mt-4 rounded-md border border-rose-700 bg-rose-950/40 p-3 text-sm text-rose-300">
          {error}
        </div>
      )}
      {result && (
        <div className="mt-6 space-y-4">
          {/* Disclaimer */}
          <div className="rounded-md border border-amber-700/60 bg-amber-950/30 p-3 text-xs text-amber-200">
            <strong className="font-semibold">AI-generated draft.</strong> This is a starting
            point grounded in your uploaded documents and must be reviewed and verified by a
            qualified professional before any use.{" "}
            <span
              className={
                result.confidence === "high"
                  ? "text-emerald-300"
                  : result.confidence === "medium"
                  ? "text-amber-300"
                  : "text-rose-300"
              }
            >
              Evidence confidence: {result.confidence}.
            </span>
          </div>

          {/* Draft editor */}
          <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                Draft
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={() => void copyDraft()}
                  className="rounded-md border border-slate-700 px-3 py-1 text-xs text-slate-300 hover:bg-slate-800"
                >
                  {copied ? "Copied!" : "Copy"}
                </button>
                <button
                  onClick={downloadDraft}
                  className="rounded-md border border-slate-700 px-3 py-1 text-xs text-slate-300 hover:bg-slate-800"
                >
                  Download .txt
                </button>
              </div>
            </div>
            <textarea
              value={draftBody}
              onChange={(e) => setDraftBody(e.target.value)}
              rows={20}
              className="mt-3 w-full resize-y rounded-md border border-slate-700 bg-slate-950/60 px-3 py-3 font-mono text-sm leading-relaxed text-slate-200 focus:border-amber-500/60 focus:outline-none"
            />
            <p className="mt-2 text-xs text-slate-500">
              Citations appear inline as [chunk_id]. Click a chunk below to inspect the source.
            </p>
          </section>

          {/* Verified claims */}
          <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Verified claims ({result.claims.length})
            </h2>
            {result.claims.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500">
                No claims could be verified against the evidence.
              </p>
            ) : (
              <ul className="mt-3 space-y-2">
                {result.claims.map((c, i) => (
                  <li key={i} className="text-sm text-slate-300">
                    <span className="inline-flex items-start gap-1">
                      <span className="mt-0.5 text-emerald-400">OK</span>
                      <span>{c.claim}</span>
                    </span>
                    <span className="ml-5 inline-flex flex-wrap gap-1">
                      {c.source_ids.map((id, j) => (
                        <button
                          key={j}
                          onClick={() => onOpenEvidence(id)}
                          className="mt-1 rounded bg-slate-800 px-1.5 py-0.5 text-[11px] text-amber-300 ring-1 ring-slate-700 hover:bg-slate-700"
                        >
                          {sourcesById.get(id)
                            ? `${sourcesById.get(id)!.name} p.${sourcesById.get(id)!.page}`
                            : id}
                        </button>
                      ))}
                    </span>
                  </li>
                ))}
              </ul>
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
      )}
    </div>
  );
}
