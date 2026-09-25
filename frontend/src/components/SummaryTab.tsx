"use client";

import { useEffect, useState } from "react";
import { api, type SummaryResponse } from "@/lib/api";
import { LegalNotice } from "@/components/Notices";

export function SummaryTab({ documentId }: { documentId: string }) {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.getSummary(documentId).then(setSummary).catch(() => setError(true));
  }, [documentId]);

  if (error) return <p className="text-sm text-[var(--color-attention)]">Could not load the summary. Please try again.</p>;
  if (!summary) return <p className="text-sm text-[var(--color-ink-soft)]">Reading the document…</p>;

  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-[var(--color-ink-soft)] mb-1">{summary.document_type}</p>
      <p className="leading-relaxed mb-6">{summary.summary}</p>

      <div className="grid sm:grid-cols-2 gap-6 mb-6">
        {summary.parties.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-2">Parties</h3>
            <ul className="text-sm space-y-1">
              {summary.parties.map((p, i) => (
                <li key={i} className="text-[var(--color-ink-soft)]">{p}</li>
              ))}
            </ul>
          </div>
        )}
        {summary.dates.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-2">Key dates</h3>
            <ul className="text-sm space-y-1">
              {summary.dates.map((d, i) => (
                <li key={i} className="text-[var(--color-ink-soft)]">{d}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {summary.obligations.length > 0 && (
        <div className="mb-2">
          <h3 className="text-sm font-semibold mb-2">Notable obligations</h3>
          <ul className="space-y-2">
            {summary.obligations.map((o, i) => (
              <li key={i} className="text-sm doc-panel px-3 py-2">
                {o}
              </li>
            ))}
          </ul>
        </div>
      )}

      <LegalNotice text={summary.disclaimer} />
    </div>
  );
}
