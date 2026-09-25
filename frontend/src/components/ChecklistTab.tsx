"use client";

import { useEffect, useState } from "react";
import { api, type ChecklistResponse } from "@/lib/api";
import { LegalNotice } from "@/components/Notices";

export function ChecklistTab({ documentId }: { documentId: string }) {
  const [data, setData] = useState<ChecklistResponse | null>(null);

  useEffect(() => {
    api.getChecklist(documentId).then(setData);
  }, [documentId]);

  if (!data) return <p className="text-sm text-[var(--color-ink-soft)]">Preparing your checklist…</p>;

  return (
    <div className="grid sm:grid-cols-2 gap-8">
      <div>
        <h3 className="font-serif-display font-semibold mb-3">Your situation</h3>
        <ul className="space-y-2 mb-6">
          {data.your_situation.map((s, i) => (
            <li key={i} className="text-sm flex items-center gap-2">
              <span className={`w-1.5 h-1.5 rounded-full ${s.needs_attention ? "bg-[var(--color-attention)]" : "bg-[var(--color-verified)]"}`} />
              {s.category} <span className="text-[var(--color-ink-soft)]">— page {s.page}{s.clause ? `, clause ${s.clause}` : ""}</span>
            </li>
          ))}
        </ul>

        <h3 className="font-serif-display font-semibold mb-3">Next steps</h3>
        <ul className="space-y-2">
          {data.next_steps.map((step, i) => (
            <li key={i} className="text-sm flex gap-2">
              <span className="text-[var(--color-ink-soft)]">{i + 1}.</span>
              {step}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="font-serif-display font-semibold mb-3">Questions for a lawyer</h3>
        <ol className="space-y-2 list-decimal list-inside text-sm">
          {data.questions_for_a_lawyer.map((q, i) => (
            <li key={i}>{q}</li>
          ))}
        </ol>
      </div>

      <div className="sm:col-span-2">
        <LegalNotice text={data.disclaimer} />
      </div>
    </div>
  );
}
