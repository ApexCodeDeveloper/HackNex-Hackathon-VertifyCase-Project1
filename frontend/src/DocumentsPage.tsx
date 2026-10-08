import { useRef, useState } from "react";
import { api } from "./api";
import type { DocumentMetadata } from "./types";

interface Props {
  documents: DocumentMetadata[];
  onChanged: () => void;
}

export default function DocumentsPage({ documents, onChanged }: Props) {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [message, setMessage] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const uploadFiles = async (files: FileList | File[]) => {
    const list = Array.from(files);
    if (list.length === 0) return;
    setUploading(true);
    setMessage(null);
    let succeeded = 0;
    for (const file of list) {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setMessage({ kind: "err", text: `${file.name}: only PDF files are supported.` });
        continue;
      }
      try {
        await api.uploadDocument(file);
        succeeded++;
      } catch (e) {
        setMessage({
          kind: "err",
          text: `${file.name}: ${e instanceof Error ? e.message : "upload failed"}`,
        });
      }
    }
    setUploading(false);
    if (succeeded > 0) {
      setMessage({
        kind: "ok",
        text: `Indexed ${succeeded} document${succeeded === 1 ? "" : "s"} into the knowledge base.`,
      });
      onChanged();
    }
  };

  const removeDocument = async (doc: DocumentMetadata) => {
    if (!window.confirm(`Delete "${doc.document_name}"? Its chunks will be removed from the index.`)) {
      return;
    }
    setBusyId(doc.document_id);
    setMessage(null);
    try {
      const res = await api.deleteDocument(doc.document_id);
      setMessage({ kind: "ok", text: res.message });
      onChanged();
    } catch (e) {
      setMessage({ kind: "err", text: e instanceof Error ? e.message : "Delete failed." });
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-8 py-10">
      <h1 className="text-2xl font-semibold text-slate-100">Documents</h1>
      <p className="mt-1 text-sm text-slate-400">
        Upload real PDF files. Text is extracted page by page, chunked with page provenance, and
        embedded into ChromaDB for grounded retrieval.
      </p>

      {/* Dropzone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          void uploadFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={`mt-6 cursor-pointer rounded-lg border-2 border-dashed p-10 text-center transition ${
          dragOver
            ? "border-amber-400 bg-amber-500/10"
            : "border-slate-700 bg-slate-900/50 hover:border-slate-500"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          className="hidden"
          onChange={(e) => {
            if (e.target.files) void uploadFiles(e.target.files);
            e.target.value = "";
          }}
        />
        <div className="text-sm font-medium text-slate-200">
          {uploading ? "Indexing document…" : "Drop PDFs here, or click to browse"}
        </div>
        <div className="mt-1 text-xs text-slate-500">
          Extraction runs before indexing — if indexing fails, the record is rolled back so the app
          never shows phantom documents.
        </div>
      </div>

      {message && (
        <div
          className={`mt-4 rounded-md border p-3 text-sm ${
            message.kind === "ok"
              ? "border-emerald-700 bg-emerald-950/40 text-emerald-300"
              : "border-rose-700 bg-rose-950/40 text-rose-300"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Document list */}
      <div className="mt-8">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Indexed documents ({documents.length})
        </h2>
        {documents.length === 0 ? (
          <div className="mt-4 rounded-lg border border-dashed border-slate-700 p-8 text-center text-sm text-slate-500">
            The workspace is empty. Upload your first PDF above — nothing is pre-seeded.
          </div>
        ) : (
          <ul className="mt-4 divide-y divide-slate-800 rounded-lg border border-slate-800">
            {documents.map((d) => (
              <li key={d.document_id} className="flex items-center justify-between gap-4 px-4 py-3">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium text-slate-200">
                    {d.document_name}
                  </div>
                  <div className="text-xs text-slate-500">
                    {d.page_count} page{d.page_count === 1 ? "" : "s"} · {d.chunk_count} chunks ·{" "}
                    {(d.file_size / 1024).toFixed(1)} KB · added{" "}
                    {new Date(d.created_at).toLocaleString()}
                  </div>
                </div>
                <button
                  onClick={() => void removeDocument(d)}
                  disabled={busyId === d.document_id}
                  className="shrink-0 rounded-md border border-rose-800 px-3 py-1.5 text-xs text-rose-300 hover:bg-rose-950/60 disabled:opacity-50"
                >
                  {busyId === d.document_id ? "Deleting…" : "Delete"}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

