"use client";

import { useCallback, useState } from "react";
import { ApiError, api, type Document } from "@/lib/api";

export function UploadPanel({ onUploaded }: { onUploaded: (doc: Document) => void }) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setUploading(true);
      try {
        const doc = await api.uploadDocument(file);
        onUploaded(doc);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
      } finally {
        setUploading(false);
      }
    },
    [onUploaded]
  );

  return (
    <div>
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const file = e.dataTransfer.files?.[0];
          if (file) handleFile(file);
        }}
        className={`block cursor-pointer text-center border-2 border-dashed rounded-sm px-6 py-10 transition-colors ${
          dragging ? "border-[var(--color-mark)] bg-[var(--color-mark-soft)]/30" : "border-[var(--color-rule)]"
        }`}
      >
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
            e.target.value = "";
          }}
        />
        <p className="font-medium mb-1">{uploading ? "Uploading and processing…" : "Drop a document here, or click to choose a file"}</p>
        <p className="text-sm text-[var(--color-ink-soft)]">PDF, DOCX or TXT, up to 10 MB</p>
      </label>
      {error && <p className="text-sm text-[var(--color-attention)] mt-3">{error}</p>}
    </div>
  );
}
