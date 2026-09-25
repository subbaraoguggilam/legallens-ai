"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, type Document } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { TopNav } from "@/components/TopNav";
import { UploadPanel } from "@/components/UploadPanel";

const STATUS_LABEL: Record<Document["status"], string> = {
  ready: "Ready",
  processing: "Processing",
  failed: "Failed to process",
};

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[] | null>(null);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (user) api.listDocuments().then(setDocuments);
  }, [user]);

  function toggleCompare(id: string) {
    setSelectedForCompare((cur) => {
      if (cur.includes(id)) return cur.filter((c) => c !== id);
      if (cur.length >= 2) return [cur[1], id];
      return [...cur, id];
    });
  }

  if (loading || !user) return null;

  return (
    <>
      <TopNav />
      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-10">
        <h1 className="font-serif-display text-2xl font-semibold mb-6">Your documents</h1>

        <div className="doc-panel p-6 mb-8">
          <UploadPanel onUploaded={(doc) => setDocuments((cur) => [doc, ...(cur ?? [])])} />
        </div>

        {selectedForCompare.length === 2 && (
          <div className="mb-6 flex items-center justify-between bg-[var(--color-mark-soft)]/40 border rule rounded-sm px-4 py-3">
            <span className="text-sm">Compare the two selected documents side by side.</span>
            <Link
              href={`/documents/${selectedForCompare[0]}?compareWith=${selectedForCompare[1]}`}
              className="text-sm font-medium bg-[var(--color-ink)] text-[var(--color-paper-raised)] px-4 py-1.5 rounded-sm"
            >
              Compare
            </Link>
          </div>
        )}

        {documents === null ? (
          <p className="text-sm text-[var(--color-ink-soft)]">Loading…</p>
        ) : documents.length === 0 ? (
          <p className="text-sm text-[var(--color-ink-soft)]">
            No documents yet. Upload a contract, agreement or notice to get started.
          </p>
        ) : (
          <ul className="divide-y rule doc-panel">
            {documents.map((doc) => (
              <li key={doc.id} className="flex items-center gap-4 px-5 py-4">
                <input
                  type="checkbox"
                  aria-label={`Select ${doc.filename} for comparison`}
                  checked={selectedForCompare.includes(doc.id)}
                  onChange={() => toggleCompare(doc.id)}
                  disabled={doc.status !== "ready"}
                  className="accent-[var(--color-mark)]"
                />
                <div className="flex-1 min-w-0">
                  <Link href={`/documents/${doc.id}`} className="font-medium hover:underline truncate block">
                    {doc.filename}
                  </Link>
                  <p className="text-xs text-[var(--color-ink-soft)] capitalize">
                    {doc.document_type} &middot; {doc.page_count} page{doc.page_count === 1 ? "" : "s"}
                  </p>
                </div>
                <span
                  className={`text-xs px-2 py-0.5 rounded-sm ${
                    doc.status === "ready"
                      ? "bg-[var(--color-verified-soft)] text-[var(--color-verified)]"
                      : doc.status === "failed"
                        ? "bg-[var(--color-attention-soft)] text-[var(--color-attention)]"
                        : "bg-[var(--color-rule)]/60 text-[var(--color-ink-soft)]"
                  }`}
                >
                  {STATUS_LABEL[doc.status]}
                </span>
                <button
                  onClick={async () => {
                    if (!confirm(`Delete ${doc.filename}? This cannot be undone.`)) return;
                    await api.deleteDocument(doc.id);
                    setDocuments((cur) => (cur ?? []).filter((d) => d.id !== doc.id));
                  }}
                  className="text-xs text-[var(--color-ink-soft)] hover:text-[var(--color-attention)] underline"
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}
