# Roadmap

Planning is milestone-based. A milestone is complete only when its acceptance criteria and tests pass; PR boundaries may move as review reveals risk.

## Next milestone: Dependency-aware verification kernel

### Outcome

Represent direct evidence, questionnaire answer meaning, and future dependency readiness separately, then introduce a curated dependency graph without weakening the deterministic policy boundary.

### Proposed PRs

#### PR 1 — Separate evidence status, answer value, and readiness status

- Define evidence, answer-value, readiness, polarity, review, applicability, and question-kind enums.
- Require explicit binary/free-text metadata and binary orientation.
- Allow only approved facts to authorize buyer-facing claims.
- Derive answer value deterministically, including negative, conflicting, and explicitly non-applicable evidence.
- Preserve the existing TrustPacket and frontend contract.

Acceptance criteria:

- A documented negative answer can be `SUPPORTED + NO`.
- Missing binary evidence is `DEFICIT + UNKNOWN` with no citations.
- Free-text decisions have no binary answer value.
- Candidate, rejected, and superseded facts cannot authorize claims.
- `NOT_APPLICABLE` requires approved, control-scoped evidence.
- Conflicting approved polarity is `PARTIAL + UNKNOWN`.

Tests: model validation, extraction metadata, approval eligibility, polarity/orientation, applicability scope, conflict handling, API compatibility, and existing refusal regressions.

#### PR 2 — Versioned control catalog and dependency graph foundation

- Add a small curated, versioned control catalog and required/supporting dependency data.
- Load and validate unknown IDs, duplicates, self-edges, and cycles.
- Add deterministic direct/transitive lookup and topological ordering.
- Do not integrate readiness into buyer-facing policy yet.

Acceptance criteria:

- Catalog and graph versions are available downstream.
- Invalid or cyclic graphs fail validation.
- Lookup and ordering are deterministic; no edge is model-generated.

Tests: version parsing, malformed data, validator failures, transitive dependencies, and stable ordering.

#### PR 3 — Canonical mapping and control assessment orchestration

- Map current question/fact labels to catalog IDs and fail closed for unknown controls.
- Build direct evidence assessments from policy decisions.
- Evaluate required prerequisites topologically; supporting edges remain non-blocking.

Acceptance criteria:

- Supported evidence plus ready prerequisites yields `READY`.
- Unmet required prerequisites yield `BLOCKED` without changing evidence status.
- Missing direct evidence never yields `READY` or a positive answer.

Tests: mappings, readiness matrices, transitive chains, supporting edges, unknown controls, and policy regressions.

#### PR 4 — Dependency-aware result and remediation

- Add graph version and control assessments to the core result.
- Generate one ordered remediation task per deficient control with blocker IDs.
- Keep answer text driven only by direct-evidence policy.

Tests: result schema, ordering/deduplication, blocked-supported controls, API serialization, and end-to-end packets.

#### PR 5 — Persistence and review UI alignment

- Persist and reload versioned assessments without losing provenance.
- Display evidence status separately from readiness and show blockers.
- Keep the backend as the only decision authority.

Tests: migration constraints, repository round trips, API contract, frontend lint/typecheck/build, and focused rendering tests if introduced separately.

### Milestone exit criteria

- All five PR outcomes are integrated through the demo run.
- Backend tests cover domain validation, graph validation, mapping, assessment, invariant regressions, remediation, API, and persistence.
- Frontend lint, TypeScript checking, and production build pass.
- Documentation reflects the shipped result model.

## Later milestones

### Evidence provenance hardening

Introduce first-class citations and persist transient matching/policy decisions; address duplicate quote ambiguity and conflicting evidence.

### Evaluation corpus

Expand synthetic positive and negative fixtures and establish regression thresholds before considering model-assisted extraction.

### Production foundations

Scope authentication, authorization, RLS, retention, transactionality, secure ingestion, and operational controls before using real customer data.
