"use client";

import { useState } from "react";
import { api, type AskResponse, type Citation } from "@/lib/api";
import { ConfidenceTag, LegalNotice } from "@/components/Notices";
import { EvidenceDrawer } from "@/components/EvidenceDrawer";

type Turn = { role: "user" | "assistant"; content: string; confidence?: string; citations?: Citation[] };

const SUGGESTIONS = [
  "Explain this document to me like I'm not a lawyer.",
  "What obligations do I have?",
  "Can either party end this agreement early?",
];

export function AskTab({ documentId }: { documentId: string }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [question, setQuestion] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [sending, setSending] = useState(false);
  const [evidence, setEvidence] = useState<{ page: number; quoted: string } | null>(null);

  async function send(q: string) {
    if (!q.trim() || sending) return;
    setTurns((t) => [...t, { role: "user", content: q }]);
    setQuestion("");
    setSending(true);
    try {
      const res: AskResponse = await api.ask(documentId, q, conversationId);
      setConversationId(res.conversation_id);
      setTurns((t) => [
        ...t,
        { role: "assistant", content: res.answer, confidence: res.confidence, citations: res.citations },
      ]);
    } catch {
      setTurns((t) => [
        ...t,
        { role: "assistant", content: "Something went wrong answering that. Please try again.", confidence: "insufficient_evidence" },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div>
      {turns.length === 0 && (
        <div className="mb-6">
          <p className="text-sm text-[var(--color-ink-soft)] mb-3">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="text-sm border rule rounded-sm px-3 py-1.5 hover:bg-[var(--color-paper)]"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-4 mb-6">
        {turns.map((turn, i) =>
          turn.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="bg-[var(--color-ink)] text-[var(--color-paper-raised)] rounded-sm px-4 py-2 max-w-md text-sm">
                {turn.content}
              </div>
            </div>
          ) : (
            <div key={i} className="doc-panel p-4 max-w-xl">
              {turn.confidence && <div className="mb-2">
                <ConfidenceTag confidence={turn.confidence} />
              </div>}
              <p className="text-sm leading-relaxed mb-2">{turn.content}</p>
              {turn.citations && turn.citations.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {turn.citations.map((c, ci) => (
                    <button
                      key={ci}
                      onClick={() => setEvidence({ page: c.page, quoted: c.quoted_text })}
                      className="text-xs underline decoration-[var(--color-mark)] decoration-2 underline-offset-2 hover:text-[var(--color-mark)]"
                    >
                      Page {c.page}
                      {c.clause ? `, clause ${c.clause}` : ""}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )
        )}
        {sending && <p className="text-sm text-[var(--color-ink-soft)]">Reading the document…</p>}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(question);
        }}
        className="flex gap-2"
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about this document…"
          className="flex-1 border rule rounded-sm px-3 py-2 bg-[var(--color-paper)] focus:outline-none focus:ring-2 focus:ring-[var(--color-mark)]"
        />
        <button
          type="submit"
          disabled={sending}
          className="bg-[var(--color-ink)] text-[var(--color-paper-raised)] px-4 py-2 rounded-sm text-sm font-medium disabled:opacity-60"
        >
          Ask
        </button>
      </form>

      <LegalNotice text="This response explains information found in the provided documents. It is not a substitute for advice from a qualified legal professional." />

      {evidence && (
        <EvidenceDrawer
          documentId={documentId}
          page={evidence.page}
          quotedText={evidence.quoted}
          onClose={() => setEvidence(null)}
        />
      )}
    </div>
  );
}
