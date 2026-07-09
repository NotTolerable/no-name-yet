import Link from "next/link";

const principles = [
  {
    title: "Evidence first",
    body: "Verilly only generates buyer-facing answers when source documentation supports them.",
  },
  {
    title: "Safe refusals",
    body: "Unsupported claims become visible compliance deficits instead of optimistic guesses.",
  },
  {
    title: "Actionable follow-up",
    body: "Each deficit becomes a concrete engineering or documentation task for the startup team.",
  },
];

export default function Home() {
  return (
    <>
      <section className="max-w-3xl py-12">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
          AI-risk questionnaire pre-flight
        </p>
        <h1 className="text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">
          Answer enterprise questionnaires without outrunning your evidence.
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-[var(--muted)]">
          Verilly helps early-stage B2B AI startups answer AI-risk and security
          questionnaires safely. No explicit evidence means no positive compliance claim.
        </p>
        <Link
          className="mt-8 inline-flex rounded-md bg-[var(--accent)] px-5 py-3 text-sm font-semibold text-white hover:opacity-90"
          href="/demo"
        >
          Run the sample analysis
        </Link>
      </section>

      <section className="grid gap-4 border-t border-[var(--border)] pt-10 md:grid-cols-3">
        {principles.map((principle) => (
          <article className="rounded-lg border border-[var(--border)] bg-white p-6" key={principle.title}>
            <h2 className="font-semibold">{principle.title}</h2>
            <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{principle.body}</p>
          </article>
        ))}
      </section>
    </>
  );
}
