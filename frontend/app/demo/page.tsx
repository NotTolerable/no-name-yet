"use client";

import { useState } from "react";

import type {
  Answer,
  PolicyStatus,
  Question,
  RemediationTask,
  TrustPacket,
} from "@/lib/types";

const apiBaseUrl = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

const statusStyles: Record<PolicyStatus, string> = {
  SUPPORTED: "border-emerald-200 bg-emerald-50 text-emerald-800",
  PARTIAL: "border-amber-200 bg-amber-50 text-amber-800",
  DEFICIT: "border-rose-300 bg-rose-100 text-rose-900",
};

function ResultCard({
  answer,
  question,
  remediationTask,
}: {
  answer: Answer;
  question: Question | undefined;
  remediationTask: RemediationTask | undefined;
}) {
  const isDeficit = answer.status === "DEFICIT";

  return (
    <article
      className={`rounded-lg border bg-white p-6 ${
        isDeficit ? "border-rose-300 ring-1 ring-rose-100" : "border-[var(--border)]"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
            {answer.question_id}
          </p>
          <h3 className="mt-2 max-w-2xl text-lg font-semibold">
            {question?.question_text ?? "Question text unavailable"}
          </h3>
        </div>
        <span
          className={`rounded-full border px-3 py-1 text-xs font-bold ${statusStyles[answer.status]}`}
        >
          {answer.status}
        </span>
      </div>

      <div className="mt-5">
        <h4 className="text-sm font-semibold">Buyer-ready response</h4>
        <p className="mt-2 leading-7">{answer.answer_text}</p>
      </div>

      <div className="mt-5 border-t border-[var(--border)] pt-4">
        <h4 className="text-sm font-semibold">Policy decision</h4>
        <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
          {answer.policy_reason}
        </p>
      </div>

      {answer.citations.length > 0 && (
        <div className="mt-5 border-t border-[var(--border)] pt-4">
          <h4 className="text-sm font-semibold">Citations</h4>
          <ul className="mt-2 space-y-2 text-sm leading-6 text-[var(--muted)]">
            {answer.citations.map((citation) => (
              <li className="rounded-md bg-[var(--background)] px-3 py-2" key={citation}>
                “{citation}”
              </li>
            ))}
          </ul>
        </div>
      )}

      {isDeficit && remediationTask && (
        <div className="mt-5 rounded-md border border-rose-200 bg-rose-50 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="font-semibold text-rose-950">{remediationTask.title}</h4>
            <span className="text-xs font-bold uppercase tracking-wide text-rose-700">
              {remediationTask.severity} severity
            </span>
          </div>
          <p className="mt-2 text-sm leading-6 text-rose-900">
            {remediationTask.description}
          </p>
          <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-rose-700">
            Suggested owner: {remediationTask.suggested_owner}
          </p>
        </div>
      )}
    </article>
  );
}

export default function DemoPage() {
  const [packet, setPacket] = useState<TrustPacket | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runDemo() {
    setIsRunning(true);
    setError(null);
    setPacket(null);

    try {
      const [runResponse, questionnaireResponse] = await Promise.all([
        fetch(`${apiBaseUrl}/runs/demo`, { method: "POST" }),
        fetch(`${apiBaseUrl}/demo/questionnaire`),
      ]);
      if (!runResponse.ok) {
        throw new Error(`Analysis failed with status ${runResponse.status}.`);
      }
      if (!questionnaireResponse.ok) {
        throw new Error(
          `Questionnaire loading failed with status ${questionnaireResponse.status}.`,
        );
      }

      const trustPacket: TrustPacket = await runResponse.json();
      const demoQuestions: Question[] = await questionnaireResponse.json();
      setPacket(trustPacket);
      setQuestions(demoQuestions);
      sessionStorage.setItem("verilly-demo-packet", JSON.stringify(trustPacket));
    } catch (runError) {
      setError(
        runError instanceof Error
          ? runError.message
          : "The pre-flight check could not be completed.",
      );
    } finally {
      setIsRunning(false);
    }
  }

  const counts = packet?.answers.reduce(
    (summary, answer) => {
      summary[answer.status] += 1;
      return summary;
    },
    { SUPPORTED: 0, PARTIAL: 0, DEFICIT: 0 } as Record<PolicyStatus, number>,
  );

  return (
    <section>
      <div className="mx-auto max-w-3xl text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
          Live demo
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Run an evidence-first questionnaire check
        </h1>
        <p className="mt-4 leading-7 text-[var(--muted)]">
          Verilly will compare a sample questionnaire with documented technical
          facts. Supported claims receive citations; unsupported claims become
          visible deficits and remediation tasks.
        </p>
        <button
          className="mt-8 rounded-md bg-[var(--accent)] px-6 py-3 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isRunning}
          onClick={runDemo}
          type="button"
        >
          {isRunning ? "Running Pre-Flight Check…" : "Run Pre-Flight Check"}
        </button>
      </div>

      {isRunning && (
        <div
          aria-live="polite"
          className="mx-auto mt-10 max-w-3xl rounded-lg border border-[var(--border)] bg-white p-6 text-center text-[var(--muted)]"
        >
          Extracting facts, matching evidence, and applying policy gates…
        </div>
      )}

      {error && (
        <div
          className="mx-auto mt-10 max-w-3xl rounded-lg border border-rose-300 bg-rose-50 p-6 text-rose-900"
          role="alert"
        >
          <h2 className="font-semibold">The pre-flight check could not run</h2>
          <p className="mt-2 text-sm">{error}</p>
          <p className="mt-2 text-sm">Confirm the FastAPI server is running at {apiBaseUrl}.</p>
        </div>
      )}

      {packet && counts && (
        <div className="mt-14">
          <div className="border-y border-[var(--border)] py-8">
            <p className="text-center text-sm text-[var(--muted)]">{packet.summary}</p>
            <dl className="mx-auto mt-6 grid max-w-2xl grid-cols-3 gap-3 text-center">
              {(["SUPPORTED", "PARTIAL", "DEFICIT"] as const).map((status) => (
                <div className={`rounded-lg border p-4 ${statusStyles[status]}`} key={status}>
                  <dd className="text-3xl font-semibold">{counts[status]}</dd>
                  <dt className="mt-1 text-xs font-bold tracking-wide">{status}</dt>
                </div>
              ))}
            </dl>
          </div>

          <div className="mt-10 space-y-5">
            {packet.answers.map((answer) => (
              <ResultCard
                answer={answer}
                key={answer.question_id}
                question={questions.find((question) => question.id === answer.question_id)}
                remediationTask={packet.remediation_tasks.find(
                  (task) => task.question_id === answer.question_id,
                )}
              />
            ))}
          </div>
        </div>
      )}

      {!packet && !isRunning && !error && (
        <div className="mt-12 min-h-40 rounded-lg border border-dashed border-[var(--border)] bg-white p-8 text-center">
          <h2 className="font-semibold">Trust packet results</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Run the pre-flight check to review supported answers, deficits, and evidence.
          </p>
        </div>
      )}
    </section>
  );
}
