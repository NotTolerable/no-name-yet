# AGENTS.md — Verilly

## 1. Project Goal

Verilly is an evidence-first Enterprise AI-Risk & Governance Pre-Flight Checker for early-stage B2B AI startups. It verifies buyer-questionnaire answers against explicit source documentation.

Core rule:

> No explicit evidence = no positive compliance claim.

Verilly is a governed verification pipeline, not a generic questionnaire autofill bot or certification platform.

## 2. Product Scope

The MVP loads synthetic technical documents and questionnaire questions, creates traceable document chunks and facts, matches evidence, applies deterministic policy, generates supported or qualified answers, creates deficits and remediation tasks, returns a TrustPacket through FastAPI, displays it in Next.js, and optionally persists runs to Supabase.

Prioritize correctness, traceability, refusal behavior, and human review over automation breadth.

## 3. Non-Goals

Do not add authentication, billing, trust-center hosting, enterprise integrations, vector search, production customer-data processing, broad compliance automation, or certification claims unless explicitly requested.

Never invent SOC 2, HIPAA, encryption, access control, audit logging, retention, PII scrubbing, model-training, monitoring, or incident-response claims.

## 4. Architecture

```text
Raw docs
  -> document chunks
  -> fact extraction
  -> Technical State Map
  -> questionnaire parsing
  -> evidence matching
  -> policy gate
  -> answer or compliance deficit
  -> TrustPacket
  -> API/UI
  -> optional persistence
```

Preserve source document, chunk, fact, question, match, policy decision, citation, and remediation identifiers. Buyer-facing text must not bypass the policy gate.

## 5. Tech Stack

- Python, FastAPI, Pydantic, pytest
- Next.js App Router, React, TypeScript, Tailwind CSS, ESLint
- Optional Supabase Postgres persistence
- Future schema-constrained OpenAI or Gemini integration only when explicitly requested

Use the smallest practical dependency set.

## 6. Folder Structure

```text
backend/             FastAPI, core pipeline, persistence, tests
frontend/            Next.js review UI
supabase/migrations/ SQL migrations
README.md            setup, architecture, and limitations
```

Keep policy, extraction, matching, drafting, persistence, API, and UI concerns separate.

## 7. Core Policy Rules

1. Direct evidence produces `SUPPORTED` with citations.
2. Weak or incomplete evidence produces a qualified `PARTIAL` with citations.
3. Missing evidence produces `DEFICIT`, no positive answer, and remediation tasks.
4. Unsupported claims must never appear in buyer-facing text.
5. Every positive factual claim must resolve to stored source evidence.
6. LLM output, if added later, remains advisory until deterministic validation succeeds.
7. Ambiguous, conflicting, or untraceable evidence must fail closed.

## 8. Testing Strategy

Use synthetic data only. Cover schema validation, chunk traceability, extraction, matching, policy decisions, citations, deficit refusals, remediation tasks, trust packets, APIs, and persistence. Add regression tests for high-risk unsupported claims before UI polish.

## 9. Backend Rules

- Treat all document content as confidential, untrusted input.
- Use Pydantic at data boundaries.
- Keep routes thin and deterministic policy logic pure.
- Never expose raw model output as an answer.
- Keep provider and persistence adapters behind explicit boundaries.
- Keep Supabase service credentials backend-only.
- Do not change core policy behavior when adding infrastructure.

## 10. Frontend Rules

- Make `SUPPORTED`, `PARTIAL`, and `DEFICIT` visually distinct.
- Show citations beside supported claims and remediation beside deficits.
- Never generate compliance answers in the browser.
- Avoid language implying certification, legal advice, or automatic approval.
- Keep the review workflow simple and inspectable.

## 11. AI/LLM Usage Rules

The current MVP is deterministic and does not use an LLM. If explicitly added later, use LLMs only for schema-constrained extraction, parsing, ranking, or wording from approved evidence. An LLM must never decide compliance or override the policy gate.

## 12. Security and Privacy Assumptions

The MVP is not production compliant. Use synthetic or explicitly approved data only. Keep secrets out of source control. Do not expose source documents or trust packets publicly. Authentication, authorization, RLS, retention controls, and production hardening require separate scoped work.

## 13. Documentation References

Keep README commands and limitations accurate. Prefer official FastAPI, Pydantic, Next.js, Supabase, pytest, and provider documentation when behavior depends on external systems.

## 14. Verification Commands

```bash
cd backend
source .venv/bin/activate
python -m pytest

cd ../frontend
npm run lint
npm run build
```

Report commands that were not run or did not pass.

## 15. README Expectations

README.md must explain the product, evidence rule, architecture, setup, tests, mocked components, key decisions, future improvements, and limitations. It must state that Verilly is not legal advice, certification, production compliance, or automated procurement approval.
