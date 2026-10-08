import { useMemo, useRef, useState } from "react";
import { api } from "./api";
import type { ChatResponse, DocumentMetadata, GroundedClaim } from "./types";

interface Props {
  documents: DocumentMetadata[];
  onOpenEvidence: (chunkId: string) => void;
}

interface UiMessage {
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
}

export default function ResearchPage({ documents, onOpenEvidence }: Props) {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const sourcesById = useMemo(() => {
    const map = new Map<string, { name: string; page: number }>();
    for (const m of messages) {
      for (const s of m.response?.sources ?? []) {
        map.set(s.chunk_id, { name: s.document_name, page: s.page_number });
      }
    }
    return map;
  }, [messages]);

  const toggleDoc = (id: string) => {
    setSelectedDocs((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(null);
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    try {
      const res = await api.chat({
        message: text,
        conversation_id: conversationId,
        document_ids: selectedDocs.length > 0 ? selectedDocs : null,
      });
      setConversationId(res.conversation_id);
      setMessages((prev) => [...prev, { role: "assistant", content: res.answer, response: res }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed.");
    } finally {
      setBusy(false);
      window.setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  };

  const newConversation = () => {
    setMessages([]);
    setConversationId(null);
    setError(null);
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-slate-800 px-8 py-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-100">Research</h1>
            <p className="mt-1 text-sm text-slate-400">
              Ask questions about your documents. Answers only contain claims verified against
              retrieved evidence — click any citation to inspect the source.
            </p>
          </div>
          <button
            onClick={newConversation}
            className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800"
          >
            New conversation
          </button>
        </div>

        {documents.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs uppercase tracking-wider text-slate-500">Scope:</span>
            <button
              onClick={() => setSelectedDocs([])}
              className={`rounded-full px-3 py-1 text-xs ring-1 transition ${
                selectedDocs.length === 0
                  ? "bg-amber-500/15 text-amber-300 ring-amber-500/40"
                  : "text-slate-400 ring-slate-700 hover:bg-slate-800"
              }`}
            >
              All documents
            </button>
            {documents.map((d) => {
              const active = selectedDocs.includes(d.document_id);
              return (
                <button
                  key={d.document_id}
                  onClick={() => toggleDoc(d.document_id)}
                  className={`rounded-full px-3 py-1 text-xs ring-1 transition ${
                    active
                      ? "bg-amber-500/15 text-amber-300 ring-amber-500/40"
                      : "text-slate-400 ring-slate-700 hover:bg-slate-800"
                  }`}
                  title={d.document_name}
                >
                  {d.document_name}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="thin-scroll flex-1 overflow-y-auto px-8 py-6">
        {messages.length === 0 && (
          <div className="mx-auto max-w-2xl rounded-lg border border-dashed border-slate-700 p-8 text-center">
            <div className="text-sm font-medium text-slate-300">Start a grounded inquiry</div>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">
              e.g. “What is the termination notice period?” — the assistant retrieves the relevant
              clauses, cites each claim to its exact source chunk, and tells you when the evidence
              is insufficient.
            </p>
          </div>
        )}

        <div className="mx-auto max-w-3xl space-y-5">
          {messages.map((m, i) =>
            m.role === "user" ? (
              <div key={i} className="flex justify-end">
                <div className="max-w-[85%] rounded-lg bg-amber-500/10 px-4 py-2.5 text-sm text-amber-100 ring-1 ring-amber-500/30">
                  {m.content}
                </div>
              </div>
            ) : (
              <AssistantMessage
                key={i}
                message={m}
                sourcesById={sourcesById}
                onOpenEvidence={onOpenEvidence}
              />
            )
          )}
          {busy && (
            <div className="text-sm italic text-slate-500">
              Retrieving evidence and verifying claims…
            </div>
          )}
          {error && (
            <div className="rounded-md border border-rose-700 bg-rose-950/40 p-3 text-sm text-rose-300">
              {error}
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Composer */}
      <div className="border-t border-slate-800 px-8 py-4">
        <div className="mx-auto flex max-w-3xl gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
            placeholder="Ask a question about the uploaded documents…"
            className="flex-1 rounded-md border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-amber-500 focus:outline-none"
          />
          <button
            onClick={() => void send()}
            disabled={busy || input.trim().length === 0}
            className="rounded-md bg-amber-500 px-5 py-2.5 text-sm font-medium text-slate-950 hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? "Thinking…" : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}

function AssistantMessage({
  message,
  sourcesById,
  onOpenEvidence,
}: {
  message: UiMessage;
  sourcesById: Map<string, { name: string; page: number }>;
  onOpenEvidence: (chunkId: string) => void;
}) {
  const res = message.response;
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Assistant
        </span>
        {res && <ConfidenceBadge confidence={res.confidence} />}
      </div>

      <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-200">
        {message.content}
      </p>

      {res && res.claims.length > 0 && (
        <div className="mt-3">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Verified claims
          </div>
          <ul className="mt-1.5 space-y-1.5">
            {res.claims.map((c, idx) => (
              <ClaimRow
                key={idx}
                claim={c}
                sourcesById={sourcesById}
                onOpenEvidence={onOpenEvidence}
              />
            ))}
          </ul>
        </div>
      )}

      {res && res.missing_information.length > 0 && (
        <div className="mt-3 rounded-md border border-amber-700/50 bg-amber-950/20 p-2.5">
          <div className="text-xs font-semibold uppercase tracking-wider text-amber-400">
            Missing from evidence
          </div>
          <ul className="mt-1 list-inside list-disc text-xs text-amber-200/90">
            {res.missing_information.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </div>
      )}

      {res && res.sources.length > 0 && (
        <div className="mt-3 text-xs text-slate-500">
          Retrieved {res.sources.length} chunk{res.sources.length === 1 ? "" : "s"} —{" "}
          {res.sources.slice(0, 3).map((s, i) => (
            <span key={s.chunk_id}>
              {i > 0 && ", "}
              <button
                onClick={() => onOpenEvidence(s.chunk_id)}
                className="text-slate-400 underline decoration-dotted hover:text-amber-300"
              >
                {s.document_name} p.{s.page_number}
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ClaimRow({
  claim,
  sourcesById,
  onOpenEvidence,
}: {
  claim: GroundedClaim;
  sourcesById: Map<string, { name: string; page: number }>;
  onOpenEvidence: (chunkId: string) => void;
}) {
  return (
    <li className="text-sm text-slate-300">
      <span className="mr-1 text-emerald-400">✓</span>
      {claim.claim}{" "}
      {claim.source_ids.map((id, i) => {
        const src = sourcesById.get(id);
        return (
          <span key={id}>
            {i > 0 && " "}
            <button
              onClick={() => onOpenEvidence(id)}
              className="ml-1 rounded bg-slate-800 px-1.5 py-0.5 text-[11px] text-amber-300 ring-1 ring-slate-700 hover:bg-slate-700"
              title={`Open source evidence: ${id}`}
            >
              {src ? `${src.name} p.${src.page}` : `src ${i + 1}`}
            </button>
          </span>
        );
      })}
    </li>
  );
}

function ConfidenceBadge({ confidence }: { confidence: string }) {
  const cls =
    confidence === "high"
      ? "text-emerald-400 ring-emerald-700"
      : confidence === "medium"
        ? "text-amber-400 ring-amber-700"
        : "text-rose-400 ring-rose-700";
  return (
    <span className={`rounded-full px-2 py-0.5 text-[11px] uppercase tracking-wider ring-1 ${cls}`}>
      {confidence} confidence
    </span>
  );
}
