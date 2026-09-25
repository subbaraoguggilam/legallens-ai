"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export function EvidenceDrawer({
  documentId,
  page,
  quotedText,
  onClose,
}: {
  documentId: string;
  page: number;
  quotedText?: string;
  onClose: () => void;
}) {
  const [text, setText] = useState<string | null>(null);
  const [pageCount, setPageCount] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(page);

  useEffect(() => {
    api.getPage(documentId, currentPage).then((res) => {
      setText(res.text);
      setPageCount(res.page_count);
    });
  }, [documentId, currentPage]);

  const parts = quotedText && text ? splitAround(text, quotedText) : null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/20" onClick={onClose}>
      <aside
        className="w-full max-w-md h-full bg-[var(--color-paper-raised)] border-l rule shadow-xl overflow-y-auto p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-serif-display text-lg font-semibold">Source, page {currentPage}</h2>
          <button onClick={onClose} className="text-sm text-[var(--color-ink-soft)] hover:text-[var(--color-ink)]">
            Close
          </button>
        </div>

        <div className="flex items-center gap-2 mb-4 text-xs">
          <button
            disabled={currentPage <= 1}
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            className="px-2 py-1 border rule rounded-sm disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-[var(--color-ink-soft)]">
            Page {currentPage} of {pageCount ?? "…"}
          </span>
          <button
            disabled={pageCount === null || currentPage >= pageCount}
            onClick={() => setCurrentPage((p) => p + 1)}
            className="px-2 py-1 border rule rounded-sm disabled:opacity-40"
          >
            Next
          </button>
        </div>

        {text === null ? (
          <p className="text-sm text-[var(--color-ink-soft)]">Loading…</p>
        ) : (
          <p className="whitespace-pre-wrap leading-relaxed text-sm">
            {parts ? (
              <>
                {parts.before}
                <span className="evidence-highlight">{parts.match}</span>
                {parts.after}
              </>
            ) : (
              text || "This page has no extracted text."
            )}
          </p>
        )}
      </aside>
    </div>
  );
}

function splitAround(text: string, needle: string): { before: string; match: string; after: string } | null {
  const cleaned = needle.replace(/…$/, "").trim();
  if (cleaned.length < 8) return null;
  const idx = text.indexOf(cleaned);
  if (idx === -1) return null;
  return { before: text.slice(0, idx), match: text.slice(idx, idx + cleaned.length), after: text.slice(idx + cleaned.length) };
}
