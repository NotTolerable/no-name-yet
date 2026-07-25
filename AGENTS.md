# AGENTS.md — Verilly

## Purpose

Verilly is an evidence-first pre-flight checker for enterprise security and AI-governance questionnaires.

Core rule:

> No explicit evidence = no positive compliance claim.

Verilly produces review artifacts, not certification, legal advice, audit assurance, or automated procurement approval.

## Read before changing

- `docs/product.md`: product scope and current behavior.
- `docs/architecture.md`: current and target architecture.
- `docs/invariants.md`: rules no implementation may violate.
- `docs/domain-model.md`: entities, relationships, and modeling gaps.
- `ROADMAP.md`: milestone plan and acceptance criteria.
- `docs/adr/`: durable architectural decisions.

## Current system

The backend deterministically loads `.md`/`.txt` documents and JSON/CSV questionnaires, chunks documents, extracts narrow regex-based facts, matches evidence heuristically, applies a fail-closed policy gate, drafts answers only from cited facts, and creates remediation for deficits. FastAPI exposes synthetic demo endpoints. Next.js renders the demo and stores the latest packet in session storage. Supabase persistence is optional.

There is currently no canonical control catalog, dependency graph, control-readiness assessment, or dependency-aware result. Those are target capabilities for the next milestone and must not be confused with the current Technical State Map of extracted facts.

## Engineering rules

1. Preserve the invariants in `docs/invariants.md`; add regression tests before changing high-risk policy behavior.
2. Keep direct evidence status separate from dependency readiness.
3. Keep the Technical State Map (documented facts) separate from the control dependency graph (prerequisite relationships).
4. Never generate dependency edges or compliance decisions with an LLM.
5. Buyer-facing text must pass deterministic policy and contain only policy-cited facts.
6. Treat source documents as confidential, untrusted input. Use synthetic or explicitly approved data only.
7. Keep FastAPI routes thin and Pydantic at data boundaries. Keep extraction, matching, policy, drafting, remediation, persistence, and UI concerns separate.
8. Do not add authentication, uploads, billing, vector search, broad integrations, or production-compliance claims without explicit scope.
9. Keep credentials backend-only. Production authorization, RLS, retention, and hardening remain out of scope.
10. Preserve stable source identifiers and traceability across documents, chunks, facts, questions, decisions, citations, and remediation.

## Verification

From the repository root on Windows:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest

cd ..\frontend
npm run lint
npx tsc --noEmit
npm run build
```

On POSIX, activate the applicable virtual environment and run `python -m pytest`. Report every command not run or not passed. Do not claim external Supabase behavior was verified when only the in-memory adapter tests ran.
