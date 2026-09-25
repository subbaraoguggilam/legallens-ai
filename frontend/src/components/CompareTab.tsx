"use client";

import { useEffect, useState } from "react";
import { api, type CompareResponse } from "@/lib/api";
import { LegalNotice } from "@/components/Notices";

export function CompareTab({ documentIdA, documentIdB }: { documentIdA: string; documentIdB: string }) {
  const [data, setData] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.compare(documentIdA, documentIdB).then(setData).catch((e) => setError(e.message ?? "Comparison failed."));
  }, [documentIdA, documentIdB]);

  if (error) return <p className="text-sm text-[var(--color-attention)]">{error}</p>;
  if (!data) return <p className="text-sm text-[var(--color-ink-soft)]">Comparing documents…</p>;

  return (
    <div>
      <div className="grid grid-cols-3 text-sm font-semibold border-b rule pb-2 mb-2">
        <span>Category</span>
        <span className="truncate">{data.document_a.filename}</span>
        <span className="truncate">{data.document_b.filename}</span>
      </div>
      <div className="divide-y rule">
        {data.rows.map((row) => (
          <div key={row.category} className={`grid grid-cols-3 text-sm py-2.5 ${row.differs ? "bg-[var(--color-mark-soft)]/25" : ""}`}>
            <span className="font-medium">{row.category}</span>
            <span>
              {row.a.value}
              {row.a.page && <span className="block text-xs text-[var(--color-ink-soft)]">p.{row.a.page}{row.a.clause ? `, ${row.a.clause}` : ""}</span>}
            </span>
            <span>
              {row.b.value}
              {row.b.page && <span className="block text-xs text-[var(--color-ink-soft)]">p.{row.b.page}{row.b.clause ? `, ${row.b.clause}` : ""}</span>}
            </span>
          </div>
        ))}
      </div>
      <p className="text-sm text-[var(--color-ink-soft)] mt-4">{data.note}</p>
      <LegalNotice text={data.disclaimer} />
    </div>
  );
}
