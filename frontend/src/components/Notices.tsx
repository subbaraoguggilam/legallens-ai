export function LegalNotice({ text }: { text: string }) {
  return (
    <p className="text-xs leading-relaxed text-[var(--color-ink-soft)] border-t rule pt-3 mt-4">
      {text}
    </p>
  );
}

export function ConfidenceTag({ confidence }: { confidence: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    document_supported: { label: "Supported by the document", cls: "bg-[var(--color-verified-soft)] text-[var(--color-verified)]" },
    professional_review_recommended: {
      label: "Professional review recommended",
      cls: "bg-[var(--color-attention-soft)] text-[var(--color-attention)]",
    },
    insufficient_evidence: { label: "Not found in the document", cls: "bg-[var(--color-rule)]/60 text-[var(--color-ink-soft)]" },
    general_information: { label: "General information", cls: "bg-[var(--color-rule)]/60 text-[var(--color-ink-soft)]" },
  };
  const entry = map[confidence] ?? map.general_information;
  return (
    <span className={`inline-block text-[11px] px-2 py-0.5 rounded-sm font-medium ${entry.cls}`}>{entry.label}</span>
  );
}
