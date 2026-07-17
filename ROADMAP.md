# Roadmap

Planning is milestone-based. A milestone is complete only when its acceptance criteria and tests pass; PR boundaries may move as code review reveals risk.

## Next milestone: Dependency-aware verification kernel

### Outcome

Integrate the existing curated dependency graph into deterministic verification so a run reports direct evidence separately from readiness and produces prerequisite-aware remediation. Preserve all current answer protections.

### Proposed PRs

#### PR 1 — Canonical control vocabulary and graph contract

- Define an explicit mapping from current question/fact labels to catalog IDs.
- Return catalog/dependency version from loaders instead of discarding it.
- Define behavior for unknown/unmapped controls and fail closed where readiness is requested.
- Tighten graph API typing and deterministic ordering.

Acceptance criteria:

- Every demo control is mapped or explicitly classified as outside the catalog.
- Graph version is available to downstream results.
- Unknown IDs, duplicate catalog IDs/edges, self-edges, and cycles fail validation.
- Mapping and graph output are deterministic.

Tests: mapping table cases, version parsing, malformed data, all validator failures, stable ordering.

#### PR 2 — Full control assessment orchestration

- Build direct evidence statuses from existing policy decisions without changing answer authorization.
- Evaluate required prerequisites in topological order.
- Keep supporting dependencies explanatory and non-blocking.
- Define missing-direct-evidence behavior for controls with and without blockers.

Acceptance criteria:

- Supported evidence plus ready required prerequisites yields `READY`.
- Supported or partial evidence with an unmet required prerequisite yields `BLOCKED`.
- Missing direct evidence never yields `READY` or a positive answer.
- Identical inputs and graph version yield identical assessments.

Tests: ready/incomplete/blocked matrices, transitive chains, supporting edges, missing assessments, regression tests for SOC 2/HIPAA and no-evidence refusal.

#### PR 3 — Dependency-aware result and remediation

- Add graph version and control assessments to the core verification result.
- Generate one remediation task per deficient/incomplete control, identify blockers, and order prerequisites first.
- Resolve question-oriented versus control-oriented remediation identity.
- Keep answer text driven solely by existing policy decisions.

Acceptance criteria:

- Results expose evidence status, readiness, citations, missing required dependencies, reasons, and graph version.
- Prerequisite tasks precede dependent tasks with no duplicate control tasks.
- A blocked supported control remains cited but is not described as ready.
- Existing no-evidence answers remain unchanged.

Tests: result schema, task ordering/deduplication, blocked-supported scenario, API serialization, end-to-end regression packet.

#### PR 4 — Persistence and review UI alignment

- Persist and reload the versioned assessment/remediation result without losing identifiers.
- Display evidence status separately from readiness and show prerequisite blockers.
- Update frontend types and avoid browser-side compliance decisions.

Acceptance criteria:

- Save/load round trips retain graph version, assessments, fact references, control IDs, and blockers.
- UI visually distinguishes evidence status from readiness and shows ordered remediation.
- Backend remains the only decision authority.

Tests: migration constraints, repository round trip, API contract, frontend lint/typecheck/build, focused rendering tests if a test framework is introduced separately.

### Milestone exit criteria

- All four PR outcomes are integrated through the demo run.
- Backend tests cover graph validation, canonical mapping, assessment matrices, invariant regressions, remediation ordering, API, and persistence.
- Frontend lint, TypeScript checking, and production build pass.
- Documentation reflects the shipped result model and any accepted tradeoffs.

## Later milestones

### Evidence provenance hardening

Introduce first-class citations and persist transient matching/policy decisions; address duplicate quote ambiguity and conflicting evidence.

### Evaluation corpus

Expand synthetic positive and negative fixtures, measure extraction/matching behavior, and establish regression thresholds before considering model-assisted extraction.

### Production foundations

Scope authentication, authorization, RLS, retention, transactionality, secure ingestion, and operational controls. This is required before real customer data, not part of the current MVP.

