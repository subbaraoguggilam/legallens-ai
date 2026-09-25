import Link from "next/link";

export default function Home() {
  return (
    <main className="flex-1 flex flex-col">
      <div className="max-w-3xl mx-auto px-6 pt-24 pb-16 w-full">
        <p className="text-sm text-[var(--color-ink-soft)] mb-4">Legal information & document assistance</p>
        <h1 className="font-serif-display text-5xl leading-[1.05] font-semibold mb-6">
          Understand what you&rsquo;re signing, in your own words.
        </h1>
        <p className="text-lg text-[var(--color-ink-soft)] max-w-xl leading-relaxed mb-10">
          Upload an employment contract, rental agreement or NDA. LegalLens AI explains it in plain
          language, points to the exact page and clause behind every answer, flags terms worth a
          second look, and prepares the questions to bring to a lawyer.
        </p>
        <div className="flex gap-4 mb-16">
          <Link
            href="/signup"
            className="bg-[var(--color-ink)] text-[var(--color-paper-raised)] px-5 py-2.5 rounded-sm text-sm font-medium hover:opacity-90"
          >
            Create an account
          </Link>
          <Link
            href="/login"
            className="border rule px-5 py-2.5 rounded-sm text-sm font-medium hover:bg-[var(--color-paper-raised)]"
          >
            Sign in
          </Link>
        </div>

        <div className="doc-panel p-6">
          <p className="text-sm text-[var(--color-ink-soft)] mb-3">Example, drawn from an uploaded agreement</p>
          <p className="mb-3">
            <span className="evidence-highlight">
              &ldquo;Either party may terminate this agreement by providing sixty (60) days written notice.&rdquo;
            </span>
          </p>
          <p className="text-xs text-[var(--color-ink-soft)]">Page 1, clause 8.1 &mdash; shown next to every answer that relies on it.</p>
        </div>

        <p className="text-xs text-[var(--color-ink-soft)] mt-10 max-w-xl leading-relaxed">
          LegalLens AI provides legal information and document assistance. It is not intended to
          replace a qualified legal professional.
        </p>
      </div>
    </main>
  );
}
