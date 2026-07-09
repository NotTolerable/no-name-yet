import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Verilly",
  description: "Evidence-backed AI-risk and security questionnaire review.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-[var(--border)] bg-white">
          <nav className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
            <Link className="text-lg font-semibold tracking-tight" href="/">
              Verilly
            </Link>
            <div className="flex gap-6 text-sm text-[var(--muted)]">
              <Link className="hover:text-[var(--foreground)]" href="/demo">
                Demo
              </Link>
              <Link className="hover:text-[var(--foreground)]" href="/results">
                Results
              </Link>
            </div>
          </nav>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-16">{children}</main>
      </body>
    </html>
  );
}
