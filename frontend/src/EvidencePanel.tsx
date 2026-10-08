import type { EvidenceChunk } from "./types";

interface Props {
  chunk: EvidenceChunk | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

export default function EvidencePanel({ chunk, loading, error, onClose }: Props) {
  return (
    <div className="absolute inset-y-0 right-0 z-20 flex w-[420px] max-w-full flex-col border-l border-slate-800 bg-slate-900 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-amber-400">
            Source Evidence
          </div>
          <div className="text-xs text-slate-500">Verbatim chunk from the uploaded document</div>
        </div>
        <button
          onClick={onClose}
          className="rounded-md px-2 py-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          aria-label="Close evidence panel"
        >
          ✕
        </button>
      </div>

      <div className="thin-scroll flex-1 overflow-y-auto p-4">
        {loading && <div className="text-sm text-slate-400">Loading evidence…</div>}
        {error && (
          <div className="rounded-md border border-rose-700 bg-rose-950/40 p-3 text-sm text-rose-300">
            {error}
          </div>
        )}
        {chunk && (
          <div className="space-y-3">
            <div className="rounded-md border border-slate-800 bg-slate-950/60 p-3 text-xs">
              <div className="flex justify-between gap-2">
                <span className="text-slate-500">Document</span>
                <span className="text-right font-medium text-slate-200">{chunk.document_name}</span>
              </div>
              <div className="mt-1 flex justify-between">
                <span className="text-slate-500">Page</span>
                <span className="text-slate-200">{chunk.page_number}</span>
              </div>
              {chunk.section && (
                <div className="mt-1 flex justify-between">
                  <span className="text-slate-500">Section</span>
                  <span className="text-slate-200">{chunk.section}</span>
                </div>
              )}
              <div className="mt-1 flex justify-between">
                <span className="text-slate-500">Relevance</span>
                <span className="text-slate-200">
                  {chunk.relevance_score != null ? chunk.relevance_score.toFixed(3) : "—"}
                </span>
              </div>
              <div className="mt-1 flex justify-between gap-2">
                <span className="shrink-0 text-slate-500">Chunk ID</span>
                <span className="break-all text-right text-slate-400">{chunk.chunk_id}</span>
              </div>
            </div>

            <div>
              <div className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                Extracted Text
              </div>
              <pre className="whitespace-pre-wrap rounded-md border border-slate-800 bg-slate-950 p-3 font-mono text-xs leading-relaxed text-slate-300">
                {chunk.text}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
