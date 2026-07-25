# Roadmap

Planning is milestone-based. A milestone is complete only when its acceptance criteria and tests pass; PR boundaries may move as review reveals risk. Ownership boundaries are defined in [docs/workstreams.md](docs/workstreams.md).

## Next milestone: Dependency-aware verification kernel

### Outcome

Represent direct evidence, questionnaire answer meaning, and dependency readiness separately; introduce a curated control graph; then expose the kernel through stable workflow contracts without weakening the deterministic policy boundary.

The PRs below are ordered dependencies. PR 1 must be completed and merged before graph integration. PR 4 may begin once PR 3's public interfaces are stable. Later PRs must consume those interfaces rather than reproduce domain logic.

### PR 1 — Correct domain semantics

**Owner:** Core/domain owner

**Scope:**

- Evidence status and answer value.
- Readiness status type.
- Fact polarity, review status, and applicability.
- Explicit binary and free-text question semantics.
- Safe `NOT_APPLICABLE` behavior.

**Acceptance criteria:**

- A documented negative answer can be `SUPPORTED + NO`.
- Missing binary evidence is `DEFICIT + UNKNOWN` with no citations.
- Free-text decisions have no binary answer value.
- Candidate, rejected, and superseded facts cannot authorize claims.
- `NOT_APPLICABLE` requires approved, control-scoped evidence.
- Conflicting approved polarity is `PARTIAL + UNKNOWN`.
- The existing external `TrustPacket` and frontend contract remain compatible.

**Required tests:** Model validation, extraction metadata, approval eligibility, polarity and orientation, applicability scope, conflict handling, API compatibility, and existing refusal regressions.

### PR 2 — Versioned control catalog and dependency graph

**Owner:** Core/domain owner

**Scope:**

- Control and dependency definitions.
- Catalog versioning.
- Graph validation.
- Direct and transitive dependency lookup.
- Deterministic topological ordering.

No workflow, persistence, frontend, or AI integration belongs in this PR.

**Acceptance criteria:**

- Catalog and graph versions are explicit and available downstream.
- Unknown control IDs, self-edges, duplicate edges, and cycles fail validation.
- Direct and transitive lookups are deterministic.
- Topological ordering is stable for identical inputs.
- Dependency edges are curated data and are never model-generated.

**Required tests:** Version parsing, malformed catalog and dependency data, every validator failure mode, direct and transitive dependencies, and stable topological ordering.

### PR 3 — Dependency-aware control assessment

**Owner:** Core/domain owner

**Scope:**

- Combine direct-evidence decisions with dependency readiness.
- Create `ControlAssessment`.
- Identify blocking required dependencies.
- Preserve the separation between evidence and readiness.
- Generate deduplicated, dependency-ordered remediation.

**Acceptance criteria:**

- Supported evidence with ready required prerequisites yields `READY`.
- Unmet required prerequisites yield `BLOCKED` without changing evidence status or answer value.
- Supporting dependencies do not automatically block readiness.
- Missing direct evidence never yields `READY` or a positive answer.
- Prerequisite remediation precedes dependent remediation, with one task per control.
- Unknown canonical controls fail closed.

**Required tests:** Readiness matrices, required and supporting edges, transitive blockers, canonical mappings, unknown controls, remediation ordering and deduplication, result serialization, and policy invariant regressions.

### PR 4 — Application workflow contracts

**Owner:** Workflow/integration owner

**Scope:**

- Application service interfaces.
- Workflow phases and legal state transitions.
- Workflow state schema.
- Fake in-memory service implementations.
- Framework-independent orchestration tests.

This PR may begin once PR 3's public interfaces are stable. It does not require or introduce LangGraph.

**Acceptance criteria:**

- Workflow contracts call the deterministic kernel through explicit interfaces.
- Workflow state has defined legal transitions and stable domain identifiers.
- Fake services exercise successful, failed, and review-required paths.
- Framework and infrastructure types do not leak into the kernel.
- Repeating an idempotent operation does not duplicate durable intent.

**Required tests:** Interface contract tests, legal and illegal transition tests, fake-service orchestration tests, idempotency cases, and kernel-boundary import checks where practical.

### PR 5 — LangGraph orchestration

**Owner:** Workflow/integration owner

**Scope:**

- LangGraph graph definition.
- Narrow workflow nodes.
- Bounded retries.
- Progress events.
- Checkpoint-compatible state.
- Fake services first.

LangGraph must call the deterministic kernel rather than reimplement it.

**Acceptance criteria:**

- Nodes delegate domain decisions to kernel interfaces.
- Legal transitions match the workflow contracts from PR 4.
- Transient failures retry within explicit limits; claim-safety failures fail closed.
- Progress events identify the run and phase without exposing sensitive content.
- Workflow state can be serialized for checkpointing.

**Required tests:** Graph construction, node delegation, transition paths, retry exhaustion, progress events, serialization, and fake-service end-to-end execution.

### PR 6 — Human-review interrupts

**Owner:** Workflow/integration owner

**Scope:**

- Fact-review pause and resume.
- Mapping-review pause where required.
- Export-approval pause and resume.
- Interruption and recovery behavior.

**Acceptance criteria:**

- Candidate facts cannot become eligible before explicit approval.
- Uncertain mappings pause without inventing a control.
- Buyer-facing export cannot complete without explicit approval.
- Resume continues from the correct phase without duplicating completed work.
- Rejected or stale review input fails safely and remains auditable.

**Required tests:** Each interrupt and resume path, rejected reviews, stale review tokens or versions, duplicate resume requests, checkpoint recovery, and export-approval enforcement.

### PR 7 — Structured AI services

**Owner:** Shared review required; implementation ownership is declared on the issue.

**Scope:**

- Pydantic-validated candidate-fact extraction.
- Proposed question-to-control mapping.
- Bounded answer drafting.
- Direct provider SDK or narrow LangChain integration.
- Deterministic post-generation validation.

AI output remains non-authoritative.

**Acceptance criteria:**

- Extraction emits candidates, never approved facts.
- Mapping proposals reference only catalog controls and remain subject to review and validation.
- Drafts use only authorized decisions, facts, and citations.
- Malformed, invented, or unsupported output fails closed.
- Provider-specific code remains outside the deterministic kernel.

**Required tests:** Structured-output validation, malformed and adversarial outputs, invented controls, unauthorized claims, provider failures, deterministic post-validation, and fake-provider contract tests.

### PR 8 — Persistence and product integration

**Owner:** Shared ownership; one primary owner is declared for each issue and PR.

**Scope:**

- Supabase business records.
- LangGraph checkpoint persistence.
- FastAPI workflow endpoints.
- Next.js workflow UI.
- Audit events.
- Progress reporting.

**Acceptance criteria:**

- Durable business records remain separate from workflow checkpoints.
- Facts, reviews, mappings, assessments, citations, remediation, and approvals retain provenance.
- API and UI expose evidence status separately from answer value and readiness.
- Workflow progress and resume behavior survive process boundaries.
- Backend authorization remains the decision boundary; frontend state cannot authorize claims.
- Persistence and API changes are migration-safe and do not expose service credentials.

**Required tests:** Repository round trips, migration constraints, checkpoint integration, API contracts, authorization and tenant-boundary cases when introduced, audit events, progress streaming, frontend rendering, frontend lint and typecheck, production build, and synthetic end-to-end trust-packet flow.

### Milestone exit criteria

- All eight PR outcomes are integrated through the verification workflow.
- The deterministic kernel remains independently testable without workflow frameworks, AI providers, FastAPI, Supabase, frontend code, or network access.
- Backend tests cover domain and graph validation, assessment, policy invariants, remediation, workflow contracts, orchestration, persistence, and API behavior.
- Frontend lint, TypeScript checking, and production build pass.
- Documentation reflects the shipped result, workflow, ownership, and persistence contracts.

## Later milestones

### Evidence provenance hardening

Introduce first-class citations and persist transient matching and policy decisions; address duplicate quote ambiguity and conflicting evidence.

### Evaluation corpus

Expand synthetic positive and negative fixtures and establish regression thresholds before relying on model-assisted extraction.

### Production foundations

Complete authentication, authorization, RLS, retention, transactionality, secure ingestion, and operational controls before using real customer data.
