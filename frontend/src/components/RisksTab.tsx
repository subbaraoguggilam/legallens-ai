"use client";

import { useEffect, useState } from "react";
import { api, type RiskScanResponse } from "@/lib/api";
import { LegalNotice } from "@/components/Notices";
import { EvidenceDrawer } from "@/components/EvidenceDrawer";

export function RisksTab({ documentId }: { documentId: string }) {
  const [data, setData] = useState<RiskScanResponse | null>(null);
  const [evidence, setEvidence] = useState<{ page: number; quoted: string } | null>(null);

  useEffect(() => {
    api.getRisks(documentId).then(setData);
  }, [documentId]);

  if (!data) return <p className="text-sm text-[var(--color-ink-soft)]">Scanning clauses…</p>;
  if (data.findings.length === 0)
    return <p className="text-sm text-[var(--color-ink-soft)]">No standard clause categories were detected in this document.</p>;

  const grouped = data.findings.reduce<Record<string, typeof data.findings>>((acc, f) => {
    (acc[f.category] ??= []).push(f);
    return acc;
  }, {});

  return (
    <div>
      <div className="space-y-5 mb-4">
        {Object.entries(grouped).map(([category, findings]) => (
          <div key={category} className="doc-panel p-4">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold text-sm">{category}</h3>
              {findings.some((f) => f.needs_attention) && (
                <span className="text-[11px] px-2 py-0.5 rounded-sm bg-[var(--color-attention-soft)] text-[var(--color-attention)]">
                  May warrant review
                </span>
              )}
            </div>
            <ul className="space-y-2">
              {findings.map((f, i) => (
                <li key={i} className="text-sm">
                  <button
                    onClick={() => setEvidence({ page: f.page, quoted: f.snippet })}
                    className="text-left hover:text-[var(--color-mark)]"
                  >
                    <span className="evidence-highlight">{f.snippet}</span>
                  </button>
                  <span className="block text-xs text-[var(--color-ink-soft)] mt-1">
                    Page {f.page}
                    {f.clause ? `, clause ${f.clause}` : ""}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <p className="text-sm text-[var(--color-ink-soft)] mb-1">{data.review_note}</p>
      <LegalNotice text={data.disclaimer} />

      {evidence && (
        <EvidenceDrawer documentId={documentId} page={evidence.page} quotedText={evidence.quoted} onClose={() => setEvidence(null)} />
      )}
    </div>
  );
}
