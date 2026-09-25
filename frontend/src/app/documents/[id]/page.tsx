"use client";

import { use, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, type Document } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { TopNav } from "@/components/TopNav";
import { SummaryTab } from "@/components/SummaryTab";
import { AskTab } from "@/components/AskTab";
import { RisksTab } from "@/components/RisksTab";
import { ChecklistTab } from "@/components/ChecklistTab";
import { CompareTab } from "@/components/CompareTab";

type TabKey = "summary" | "ask" | "risks" | "checklist" | "compare";

export default function DocumentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user, loading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const compareWith = searchParams.get("compareWith");

  const [doc, setDoc] = useState<Document | null>(null);
  const [tab, setTab] = useState<TabKey>(compareWith ? "compare" : "summary");

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (user) api.getDocument(id).then(setDoc).catch(() => setDoc(null));
  }, [user, id]);

  if (loading || !user) return null;

  const tabs: { key: TabKey; label: string }[] = [
    { key: "summary", label: "Understand" },
    { key: "ask", label: "Ask" },
    { key: "risks", label: "Risks" },
    { key: "checklist", label: "Checklist" },
    ...(compareWith ? [{ key: "compare" as const, label: "Compare" }] : []),
  ];

  return (
    <>
      <TopNav />
      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-10">
        {!doc ? (
          <p className="text-sm text-[var(--color-ink-soft)]">Loading document…</p>
        ) : doc.status !== "ready" ? (
          <div className="doc-panel p-6">
            <p className="font-medium mb-1">{doc.filename}</p>
            <p className="text-sm text-[var(--color-ink-soft)]">
              {doc.status === "processing" ? "Still processing this document…" : doc.error ?? "Processing failed."}
            </p>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <h1 className="font-serif-display text-2xl font-semibold">{doc.filename}</h1>
              <p className="text-sm text-[var(--color-ink-soft)] capitalize">
                {doc.document_type} &middot; {doc.page_count} page{doc.page_count === 1 ? "" : "s"}
              </p>
              {doc.warnings.length > 0 && (
                <p className="text-xs text-[var(--color-attention)] mt-1">{doc.warnings.join(" ")}</p>
              )}
            </div>

            <nav className="flex gap-1 border-b rule mb-6">
              {tabs.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
                    tab === t.key
                      ? "border-[var(--color-mark)] text-[var(--color-ink)]"
                      : "border-transparent text-[var(--color-ink-soft)] hover:text-[var(--color-ink)]"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </nav>

            {tab === "summary" && <SummaryTab documentId={id} />}
            {tab === "ask" && <AskTab documentId={id} />}
            {tab === "risks" && <RisksTab documentId={id} />}
            {tab === "checklist" && <ChecklistTab documentId={id} />}
            {tab === "compare" && compareWith && <CompareTab documentIdA={id} documentIdB={compareWith} />}
          </>
        )}
      </main>
    </>
  );
}
