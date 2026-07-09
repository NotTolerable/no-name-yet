"use client";

import Link from "next/link";
import { useSyncExternalStore } from "react";

import type { TrustPacket } from "@/lib/types";

const statusStyles = {
  SUPPORTED: "bg-emerald-50 text-emerald-800",
  PARTIAL: "bg-amber-50 text-amber-800",
  DEFICIT: "bg-rose-50 text-rose-800",
};

function subscribeToSessionStorage(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  return () => window.removeEventListener("storage", onStoreChange);
}

function readStoredPacket() {
  return sessionStorage.getItem("verilly-demo-packet");
}

function readServerPacket() {
  return null;
}

export default function ResultsPage() {
  const storedPacket = useSyncExternalStore(
    subscribeToSessionStorage,
    readStoredPacket,
    readServerPacket,
  );
  let packet: TrustPacket | null = null;
  if (storedPacket) {
    try {
      packet = JSON.parse(storedPacket) as TrustPacket;
    } catch {
      packet = null;
    }
  }

  if (!packet) {
    return (
      <section className="rounded-lg border border-[var(--border)] bg-white p-8">
        <h1 className="text-2xl font-semibold">No analysis results yet</h1>
        <p className="mt-3 text-[var(--muted)]">Run the sample analysis to create a trust packet.</p>
        <Link className="mt-6 inline-block font-semibold text-[var(--accent)]" href="/demo">
          Go to the demo →
        </Link>
      </section>
    );
  }

  return (
    <section>
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
        Trust packet
      </p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight">Analysis results</h1>
      <p className="mt-4 text-[var(--muted)]">{packet.summary}</p>

      <div className="mt-10 space-y-4">
        {packet.answers.map((answer) => (
          <article className="rounded-lg border border-[var(--border)] bg-white p-6" key={answer.question_id}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-semibold">{answer.question_id}</h2>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusStyles[answer.status]}`}>
                {answer.status}
              </span>
            </div>
            <p className="mt-4 leading-7">{answer.answer_text}</p>
            <p className="mt-3 text-sm text-[var(--muted)]">{answer.policy_reason}</p>
            {answer.citations.length > 0 && (
              <div className="mt-5 border-t border-[var(--border)] pt-4">
                <h3 className="text-sm font-semibold">Evidence</h3>
                <ul className="mt-2 space-y-2 text-sm text-[var(--muted)]">
                  {answer.citations.map((citation) => (
                    <li key={citation}>“{citation}”</li>
                  ))}
                </ul>
              </div>
            )}
          </article>
        ))}
      </div>

      {packet.remediation_tasks.length > 0 && (
        <section className="mt-12">
          <h2 className="text-2xl font-semibold">Compliance deficits</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {packet.remediation_tasks.map((task) => (
              <article className="rounded-lg border border-[var(--border)] bg-white p-6" key={task.question_id}>
                <p className="text-xs font-semibold uppercase tracking-wide text-rose-700">
                  {task.severity} severity
                </p>
                <h3 className="mt-2 font-semibold">{task.title}</h3>
                <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{task.description}</p>
              </article>
            ))}
          </div>
        </section>
      )}
    </section>
  );
}
