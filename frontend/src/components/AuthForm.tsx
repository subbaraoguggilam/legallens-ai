"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { refresh } = useAuth();
  const router = useRouter();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "signup") {
        await api.signup(email, password);
      } else {
        await api.login(email, password);
      }
      await refresh();
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex-1 flex items-center justify-center px-6">
      <form onSubmit={onSubmit} className="doc-panel w-full max-w-sm p-8">
        <h1 className="font-serif-display text-2xl font-semibold mb-1">
          {mode === "signup" ? "Create your account" : "Welcome back"}
        </h1>
        <p className="text-sm text-[var(--color-ink-soft)] mb-6">
          {mode === "signup" ? "Documents stay private to your account." : "Sign in to your documents."}
        </p>

        <label className="block text-sm mb-1" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border rule rounded-sm px-3 py-2 mb-4 bg-[var(--color-paper)] focus:outline-none focus:ring-2 focus:ring-[var(--color-mark)]"
        />

        <label className="block text-sm mb-1" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          type="password"
          required
          minLength={mode === "signup" ? 10 : undefined}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border rule rounded-sm px-3 py-2 mb-1 bg-[var(--color-paper)] focus:outline-none focus:ring-2 focus:ring-[var(--color-mark)]"
        />
        {mode === "signup" && (
          <p className="text-xs text-[var(--color-ink-soft)] mb-4">At least 10 characters, with letters and digits.</p>
        )}

        {error && <p className="text-sm text-[var(--color-attention)] mt-3 mb-1">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full mt-5 bg-[var(--color-ink)] text-[var(--color-paper-raised)] py-2.5 rounded-sm text-sm font-medium disabled:opacity-60"
        >
          {submitting ? "Please wait…" : mode === "signup" ? "Create account" : "Sign in"}
        </button>

        <p className="text-sm text-[var(--color-ink-soft)] mt-5 text-center">
          {mode === "signup" ? (
            <>
              Already have an account?{" "}
              <Link href="/login" className="underline">
                Sign in
              </Link>
            </>
          ) : (
            <>
              New here?{" "}
              <Link href="/signup" className="underline">
                Create an account
              </Link>
            </>
          )}
        </p>
      </form>
    </main>
  );
}
