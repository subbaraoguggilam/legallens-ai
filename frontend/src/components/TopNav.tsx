"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export function TopNav() {
  const { user, logout } = useAuth();
  const router = useRouter();

  return (
    <header className="border-b rule bg-[var(--color-paper-raised)]">
      <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[var(--color-mark)]" aria-hidden />
          <span className="font-serif-display text-lg font-semibold">LegalLens AI</span>
        </Link>
        {user && (
          <div className="flex items-center gap-4 text-sm text-[var(--color-ink-soft)]">
            <span>{user.email}</span>
            <button
              onClick={async () => {
                await logout();
                router.push("/login");
              }}
              className="underline decoration-[var(--color-rule)] underline-offset-4 hover:text-[var(--color-ink)]"
            >
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
