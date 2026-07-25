# Verilly Workstreams and Ownership

Verilly uses two primary workstreams so developers can work independently without duplicating policy logic or changing shared contracts in isolation. “Owner” identifies the responsible workstream, not a hard-coded GitHub account; every issue and PR still names one person as primary owner.

## Core and domain workstream

**Primary owner:** Project architecture/core owner

Owns:

- `backend/core/models.py`;
- the control catalog and dependency graph;
- evidence eligibility and evidence matching;
- policy and claim authorization;
- control assessment;
- citation validation;
- remediation ordering;
- domain-model documentation; and
- architectural invariants.

Responsibilities:

- define what Verilly may believe and claim;
- preserve deterministic behavior;
- maintain pure, framework-independent tests; and
- publish stable interfaces for the workflow layer.

The deterministic kernel must not import workflow frameworks, AI provider SDKs, FastAPI routes, Supabase clients, frontend code, or other external-service implementations.

## Workflow and integration workstream

**Primary owner:** Workflow/integration owner

Owns:

- application service interfaces;
- workflow state and transitions;
- LangGraph nodes;
- checkpointing;
- retries and progress events;
- review interrupts;
- FastAPI workflow endpoints; and
- infrastructure adapters.

Responsibilities:

- define how verification runs execute;
- call the deterministic kernel through stable interfaces;
- preserve resumability and idempotency; and
- avoid placing policy decisions inside workflow nodes.

```text
Core owner:
What is supported, blocked, missing, or authorised?

Workflow owner:
When does each operation run, pause, retry, resume, or complete?
```

## Shared integration areas

The following areas require coordination:

- Pydantic models shared across layers;
- persistence schemas;
- API contracts;
- AI service interfaces;
- Next.js workflow integration;
- export formats;
- `ROADMAP.md`;
- `docs/architecture.md`; and
- `docs/invariants.md`.

Neither developer should independently change a shared contract. Open or update an issue, identify the proposed contract change, confirm file ownership, and request review from the other developer before merging.

Shared ownership does not mean both developers edit the same files simultaneously. Assign one primary implementer for each issue and use review for coordination.

## Conflict avoidance

- Reserve a PR-sized scope through an assigned issue before creating a branch.
- Declare shared files in the issue and check active branches for overlap.
- Prefer separate adapter and kernel PRs over a cross-layer rewrite.
- Do not copy policy conditions into workflow, API, persistence, or frontend code.
- Rebase or merge the latest `main` before beginning dependent work.
- Stop and coordinate when an implementation requires an undeclared shared-contract change.
