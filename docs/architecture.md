# Verilly Architecture

## 1. Purpose and scope

Verilly is an evidence-first verification system for enterprise security and AI-governance questionnaires. It turns reviewed source material into traceable questionnaire decisions, bounded answers, and remediation work.

The operating principle is:

```text
No eligible evidence means no supported buyer-facing claim.
```

Verilly is not an autonomous compliance agent, a compliance certification authority, a generic questionnaire autofill tool, or a substitute for legal or compliance advice. Its outputs are review artifacts.

The repository currently implements a small deterministic demo. This document describes both that implementation and a larger target architecture. Target components are explicitly labeled and should not be read as shipped capabilities. Product scope and safety rules are defined in [product.md](product.md) and [invariants.md](invariants.md).

## 2. Current architecture versus target architecture

| Area | Current state | Target state |
|---|---|---|
| Frontend | Next.js demo and results pages call the demo API and keep the latest `TrustPacket` in browser session storage. | Project, document, fact-review, mapping-review, results, remediation, export-approval, and run-progress views. |
| API | FastAPI exposes health, synthetic demo inputs, synchronous demo execution, and optional saved-run retrieval. There is no authentication, upload, review, export, or SSE API. | An authenticated transport boundary for workflow runs, reviews, results, remediation, exports, and SSE progress. |
| Evidence extraction | Local `.md` and `.txt` files are chunked and processed by narrow deterministic regex rules. The trusted extractor explicitly marks its facts approved. | Structured candidate extraction may be AI-assisted, but candidates require validation and review before becoming eligible. |
| Fact review | Review-status and applicability values exist in the domain model, but there is no review workflow, API, UI, or persistence for them. | Explicit candidate review with auditable approval, rejection, and supersession. |
| Question mapping | Questions carry free-form required-control labels. Deterministic aliases, keywords, and risk-domain heuristics match them to facts. | Proposed question-to-control mappings against a canonical catalog, with deterministic validation and human review when required. |
| Policy decisions | A deterministic gate separates internal evidence status from binary answer value and excludes non-approved facts. The external `Answer` contract exposes evidence status but not answer value. | The deterministic kernel remains the only claim-authorisation authority, with first-class citations and complete assessment semantics. |
| Dependency graph | No canonical control catalog, dependency graph, control assessment, or dependency-aware result exists. | A curated, versioned, validated, acyclic graph drives readiness and remediation order without creating evidence. |
| Workflow orchestration | `generate_trust_packet` runs synchronously in one process and loops over questions. There are no checkpoints, retries, interrupts, or progress events. | LangGraph coordinates explicit states, retries, resumability, progress, and review pauses. |
| Persistence | Optional backend-only Supabase PostgREST calls persist completed runs, documents, chunks, facts, questions, answers, and remediation tasks. Writes are sequential, not transactional; live Supabase behavior is unverified. There is no Supabase Storage integration. | Supabase Postgres stores durable business truth; Supabase Storage holds private uploads and generated exports. |
| Exports | The API returns JSON `TrustPacket` objects. There is no file export or export approval. | Approved, citation-validated export artifacts with durable approval records. |
| Observability | No product-specific tracing, workflow telemetry, or evaluation system is present. | Structured logs and metrics, workflow-level telemetry, and later LangSmith or OpenTelemetry integration without logging sensitive evidence by default. |

The current Technical State Map is an in-memory collection of extracted facts. Its labels are not yet a canonical control catalog, and its data is not a dependency graph.

## 3. Target architecture overview

The complete target architecture is:

```text
┌──────────────────────────────────────────────────────────────┐
│                         Next.js UI                           │
│                                                              │
│ Projects · Documents · Fact Review · Questionnaire Review   │
│ Results · Remediation · Export Approval · Run Progress       │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTP / SSE
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                        FastAPI API                           │
│                                                              │
│ Authentication · Request validation · Run endpoints          │
│ Review endpoints · Result endpoints · Export endpoints       │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  Application / Workflow Layer                │
│                         LangGraph                            │
│                                                              │
│ Ingest → Extract → Fact review → Map controls → Verify       │
│ → Assess dependencies → Draft → Export review → Export       │
│                                                              │
│ Checkpointing · Resume · Retries · Progress · Interrupts      │
└───────────────┬──────────────────────────────┬───────────────┘
                │                              │
                ▼                              ▼
┌────────────────────────────┐    ┌────────────────────────────┐
│ Deterministic Domain Kernel│    │       AI Service Layer     │
│                            │    │                            │
│ Pydantic domain models     │    │ LLM fact extraction        │
│ Evidence eligibility       │    │ Question-control mapping   │
│ Evidence matching          │    │ Bounded answer drafting    │
│ Claim authorization        │    │                            │
│ Dependency readiness       │    │ LangChain optional         │
│ Remediation ordering       │    │ Direct SDK also acceptable │
│ Citation validation        │    │ Pydantic structured output │
└───────────────┬────────────┘    └──────────────┬─────────────┘
                │                                │
                └────────────────┬───────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│                       Infrastructure                         │
│                                                              │
│ Supabase Postgres: durable business records                  │
│ Supabase Storage: uploaded documents and exports             │
│ LangGraph checkpointer: workflow execution checkpoints       │
│ LangSmith/OpenTelemetry later: traces and evaluations        │
└──────────────────────────────────────────────────────────────┘
```

### Next.js UI

The target UI supports project management, document upload and review, candidate-fact review, questionnaire review, question-to-control mapping review, verification results, remediation planning, export approval, and workflow progress. It may present decisions and collect review actions, but it must never independently generate or authorize compliance claims.

### FastAPI API

FastAPI is the target authentication and transport boundary. It validates requests and responses and exposes workflow-run, review, approval, results, remediation, export, and progress endpoints. SSE is appropriate for one-way progress updates where needed. Routes should delegate to application services and must not duplicate policy logic.

### Application and workflow layer

LangGraph is appropriate when the workflow needs explicit states, durable execution, resumability, bounded retries, progress events, and human-in-the-loop interrupts. Fact review and export review are deliberate pauses rather than incidental UI states.

```text
LangGraph coordinates domain operations; it does not decide what Verilly is allowed to claim.
```

Workflow nodes call stable application services. Their transitions record what happens next; domain policy determines whether evidence or a claim is valid.

### Deterministic domain kernel

The kernel is authoritative for Pydantic domain validation, fact eligibility, evidence matching, evidence status, answer value, dependency readiness, remediation ordering, citation validation, and claim authorization.

It must be independently testable without LangGraph, LangChain, an LLM, Supabase, FastAPI, or external network access. Identical inputs and pinned catalog versions must produce identical decisions.

### AI service layer

AI services may extract candidate facts, parse questionnaires, propose question-to-control mappings, draft bounded answer wording, and produce explanatory summaries. LLM output must pass Pydantic structured-output validation and remains untrusted until the applicable review and deterministic checks succeed.

AI services may not approve facts, define dependency edges, determine evidence eligibility, determine readiness, authorize buyer-facing claims, or approve exports.

LangChain is optional. It is useful only where it supplies concrete value such as provider-neutral model interfaces, structured output, prompt templates, retries, middleware, or tracing integration. Verilly is not a generic LangChain agent, and a direct provider SDK remains acceptable.

### Infrastructure

- **Supabase Postgres** is intended to hold durable product records, provenance, decisions, reviews, and approvals.
- **Supabase Storage** is intended to hold private uploaded documents and generated exports.
- **LangGraph checkpoint persistence** records workflow execution position, retry state, and resumable context.
- **LangSmith or OpenTelemetry** may later provide model and service tracing and evaluation.
- **Secrets and environment configuration** remain server-side, are environment-specific, and are never exposed through frontend variables.

## 4. Verification workflow

The target workflow is:

```text
START
  │
  ▼
Create verification run
  │
  ▼
Load uploaded documents
  │
  ▼
Parse and chunk documents
  │
  ▼
Extract candidate facts
  │
  ▼
Validate structured extraction
  │
  ▼
Pause for fact review
  │
  ▼
Store approved facts
  │
  ▼
Parse questionnaire
  │
  ▼
Propose question-to-control mappings
  │
  ▼
Review mappings when required
  │
  ▼
Match approved evidence
  │
  ▼
Evaluate direct evidence
  │
  ▼
Assess dependency readiness
  │
  ▼
Generate remediation plan
  │
  ▼
Draft bounded buyer-facing answers
  │
  ▼
Validate claims and citations
  │
  ▼
Pause for export approval
  │
  ▼
Generate trust packet
  │
  ▼
COMPLETE
```

Classification indicates the primary boundary for each stage; several stages deliberately combine orchestration with deterministic validation.

| Stage | Classification | Boundary |
|---|---|---|
| Create verification run | Infrastructure-driven | Creates durable run identity and initial workflow state. |
| Load uploaded documents | Infrastructure-driven | Reads only authorised project files from private storage. |
| Parse and chunk documents | Deterministic | Produces stable chunks and provenance identifiers. |
| Extract candidate facts | AI-assisted | Proposes structured candidates; does not approve them. |
| Validate structured extraction | Deterministic | Rejects malformed or out-of-contract output. |
| Pause for fact review | Human-reviewed | A reviewer approves, rejects, or supersedes candidates. |
| Store approved facts | Infrastructure-driven | Persists review outcome and provenance. |
| Parse questionnaire | Deterministic or AI-assisted | Uses deterministic parsers first; AI may propose structure for complex inputs. |
| Propose question-to-control mappings | AI-assisted | Produces proposals against the pinned catalog. |
| Review mappings when required | Human-reviewed | Resolves uncertain or high-impact mappings. |
| Match approved evidence | Deterministic | Excludes ineligible facts and ranks evidence reproducibly. |
| Evaluate direct evidence | Deterministic | Produces evidence status and answer value. |
| Assess dependency readiness | Deterministic | Evaluates required graph prerequisites without changing direct evidence. |
| Generate remediation plan | Deterministic | Deduplicates and topologically orders control work. |
| Draft bounded buyer-facing answers | AI-assisted | May improve wording within authorised facts and citations. |
| Validate claims and citations | Deterministic | Rejects unsupported facts, conclusions, or missing provenance. |
| Pause for export approval | Human-reviewed | Requires explicit approval of the final buyer-facing artifact. |
| Generate trust packet | Deterministic and infrastructure-driven | Builds the authorised artifact and stores its durable record. |
| Complete run | Infrastructure-driven | Finalises status while preserving audit history. |

## 5. Domain model

Pydantic is the validation and serialization layer for domain contracts at application and API boundaries. The current model is described in [domain-model.md](domain-model.md); several groups below are target additions.

### Evidence models

- `Document` represents a source file.
- `DocumentChunk` is a stable, traceable segment of a document.
- `Fact` represents a proposition linked to source evidence.
- `FactPolarity` is `POSITIVE`, `NEGATIVE`, or `NEUTRAL` relative to a canonical proposition.
- `FactReviewStatus` is `CANDIDATE`, `APPROVED`, `REJECTED`, or `SUPERSEDED`.
- `FactApplicability` records applicable, explicitly non-applicable, or unspecified scope.

The first six models and values exist today. The current trusted regex extractor explicitly emits approved facts; a future untrusted or model-based extractor must emit candidates.

### Questionnaire models

- `Question` records text, required-control label, response kind, and risk domain.
- `QuestionResponseKind` distinguishes binary from free-text questions.
- Affirmative polarity records which canonical fact polarity means `YES` for a binary question.
- A question-to-control mapping will link questions to catalog controls with provenance and review state.

The mapping is a target model. Current questions use free-form labels and deterministic aliases rather than a canonical catalog.

### Verification models

- `EvidenceMatch` links a question to a candidate supporting fact.
- `EvidenceStatus` is `SUPPORTED`, `PARTIAL`, or `DEFICIT`.
- `AnswerValue` is `YES`, `NO`, `UNKNOWN`, or `NOT_APPLICABLE` for binary decisions.
- `PolicyDecision` records direct-evidence authorization, reason, and cited fact IDs.
- `ReadinessStatus` is `READY`, `INCOMPLETE`, or `BLOCKED`.
- `ControlAssessment` will combine direct-evidence results with dependency readiness without conflating them.

Readiness values exist in the current model, but no readiness assessment is implemented or exposed.

```text
EvidenceStatus describes what the direct evidence supports.

AnswerValue describes the substantive answer to the question.

ReadinessStatus describes whether the control and its required prerequisites are operationally ready.
```

For example:

```text
Question:
“Is role-based access control implemented?”

Direct evidence:
Supported

Required dependency:
Identity management is incomplete

Result:
evidence_status = SUPPORTED
answer_value = YES
readiness_status = BLOCKED
```

### Control graph models

The target graph introduces `ControlDefinition`, `ControlDependency`, `DependencyType`, and `ControlCatalogVersion`. Catalog identifiers and versions are product knowledge. Required edges can block readiness; supporting edges can influence explanation without automatically blocking it.

### Output models

- `Answer` is the current buyer-facing rendering with status, text, citation quotations, and policy reason.
- `Citation` will become a first-class provenance record rather than only a quotation string.
- `RemediationTask` currently represents one question-level deficit; the target adds canonical control and blocker relationships.
- `TrustPacket` currently contains answers, remediation tasks, and a summary; the target also records assessment and version provenance.

### Workflow models

`VerificationRun`, `VerificationWorkflowState`, `WorkflowPhase`, `ReviewRequest`, and `WorkflowError` are target models. They should describe legal transitions, review requirements, recoverable errors, and durable references without embedding framework-specific objects into the domain kernel.

## 6. Technical State Map versus dependency graph

```text
Technical State Map
────────────────────────────────────
Records what the organisation has
based on reviewed source evidence.

Document
   ↓
Document chunk
   ↓
Approved fact
   ↓
Canonical control


Control Dependency Graph
────────────────────────────────────
Records prerequisite relationships
between canonical controls.

Identity management
   ↓ REQUIRED
Role-based access
   ↓ REQUIRED
Privileged-action logging
```

The Technical State Map is organisation-specific and derived from reviewed source evidence. The dependency graph is product knowledge shared across assessments. Facts must not be stored as graph edges, and graph edges must never be generated by an LLM.

The graph must be human-curated, deterministic, versioned, validated, and acyclic. A graph version used for an assessment must be recorded so the result can be reproduced.

## 7. Claim-authorisation boundary

```text
LLM proposes
      │
      ▼
Pydantic validates structure
      │
      ▼
Human approves evidence
      │
      ▼
Deterministic kernel evaluates
      │
      ▼
Human approves export
      │
      ▼
Buyer-facing output
```

```text
LLM proposes.
Humans review.
The deterministic kernel authorizes.
```

Generated language cannot introduce facts, controls, certifications, or conclusions absent from the authorised decision and its citations. Human approval does not override evidence eligibility or policy; it accepts an artifact that has already passed deterministic validation.

## 8. Dependency direction

```text
Next.js UI
     ↓
FastAPI transport layer
     ↓
Application services / LangGraph
     ↓
Deterministic domain kernel
     ↓
Pydantic domain models
```

Dependencies point inward. The domain kernel must not import frontend code, FastAPI route modules, LangGraph, LangChain, OpenAI or Gemini SDKs, or Supabase clients. Infrastructure and AI implementations satisfy interfaces owned by the application layer.

Conceptually, those interfaces may look like:

```python
class FactExtractionService(Protocol):
    def extract(
        self,
        chunks: list[DocumentChunk],
    ) -> list[FactCandidate]:
        ...


class AnswerDraftingService(Protocol):
    def draft(
        self,
        question: Question,
        decision: PolicyDecision,
        cited_facts: list[Fact],
    ) -> DraftAnswer:
        ...


class VerificationRepository(Protocol):
    def save_fact_candidates(
        self,
        candidates: list[FactCandidate],
    ) -> None:
        ...
```

These examples describe boundaries, not existing interfaces.

## 9. Data ownership and persistence

```text
Supabase Postgres
────────────────────────────────────
Durable product truth:
- projects
- documents
- facts
- reviews
- questions
- mappings
- assessments
- answers
- citations
- remediation tasks
- approvals
- audit events


LangGraph checkpoints
────────────────────────────────────
Workflow execution state:
- completed nodes
- interrupt position
- retry state
- resumable workflow context
```

```text
Supabase records what Verilly knows and why.

LangGraph records where a workflow stopped and how it resumes.
```

LangGraph checkpoint data must not become the only durable record of facts, decisions, approvals, or citations. Workflow state should reference durable business identifiers rather than duplicate confidential records unnecessarily.

Today, optional PostgREST persistence stores only completed demo-run records in tables from `supabase/migrations/001_initial_schema.sql`. It does not provide uploads, Storage integration, review records, mappings, assessments, approvals, audit events, transactions across a complete run, or verified production security.

## 10. Failure handling

Claim safety failures fail closed. Retry is reserved for transient operations and must not change policy outcomes.

| Failure | Expected behavior | Progress handling |
|---|---|---|
| Invalid Pydantic output | Reject the output; retry a bounded AI call if the error is repairable, otherwise pause or fail the run. Never coerce it into evidence. | Preserve validated prior stages and the validation error. |
| LLM extraction failure | Retry transient provider failures within limits, then pause for operator action or fail the extraction phase. | Preserve documents and completed chunks; create no approved facts. |
| Unsupported control ID | Fail validation or pause mapping review; do not silently create or approximate a control. | Preserve the proposed mapping and diagnostic. |
| Dependency graph validation failure | Mark the run failed before readiness assessment. Unknown IDs, duplicates, self-edges, or cycles are configuration errors. | Preserve pre-assessment work but publish no readiness result. |
| Missing evidence | Produce `DEFICIT` and, for binary questions, `UNKNOWN`; create remediation and no positive claim. | Continue the run. |
| Conflicting evidence | Produce a qualified `PARTIAL + UNKNOWN` decision and surface the conflict for review. | Continue without an unqualified answer. |
| Rejected evidence | Exclude it from matching, authorization, and drafting. | Preserve its review history for auditability. |
| Stale workflow checkpoint | Refuse unsafe resume when code, schema, or catalog compatibility cannot be established; restart from a safe durable phase if supported. | Keep business records; invalidate or migrate the checkpoint explicitly. |
| Failed export generation | Retry transient rendering/storage errors, then keep the run in an export-failed or reviewable state. | Preserve approved decisions and the approval record; do not mark complete. |
| Unavailable external model provider | Retry transient failure, permit a deterministic or manual path where defined, or pause. | Preserve partial progress and do not weaken validation. |

## 11. Security and privacy boundaries

The target system requires private document and export storage, tenant isolation at every business-record and object-storage boundary, auditable review and export approvals, configurable retention, and verified deletion of database records, storage objects, checkpoints, and derived artifacts.

Service-role keys and model-provider credentials remain server-side. They must never be embedded in frontend code or `NEXT_PUBLIC_*` variables. Access to documents and exports must be authorised independently of possession of an object identifier.

Only the minimum necessary text should be sent to external model providers. Provider configuration must account for retention, training, region, and contractual requirements. Raw documents, evidence quotations, and secrets should not enter logs by default. Demo fixtures and tests use synthetic or explicitly approved data, never real customer content.

These are target requirements, not claims about the current demo. The repository currently has no application authentication, authorization, RLS, upload path, Supabase Storage client, tenant-aware UI, retention workflow, or deletion workflow. Its backend can use a server-side Supabase service-role key for optional PostgREST persistence, and the migration explicitly defers RLS.

## 12. Observability and evaluation

Future observability should correlate structured application logs with workflow run IDs while recording phase transitions, node timing, retry counts, interrupt events, validation failures, and export outcomes. Logs should use identifiers and safe summaries rather than raw confidential text.

LangSmith may trace model calls and support extraction, mapping, and drafting evaluations. OpenTelemetry may cover broader API, workflow, persistence, and infrastructure traces. Either integration must apply redaction and sampling suitable for sensitive inputs.

Evaluation combines deterministic regression tests with structured-output validation metrics, claim-authorisation failure metrics, mapping-review rates, retry rates, and carefully curated model evaluations. Model quality metrics cannot replace fail-closed policy tests.

The current repository has no LangSmith, OpenTelemetry, workflow tracing, or dedicated evaluation telemetry.

## 13. Testing strategy

The target testing layers are:

- Pydantic model validation tests for legal and illegal states.
- Deterministic policy unit tests, especially negative and conflicting evidence.
- Dependency graph validation tests for versions, unknown IDs, duplicates, self-edges, and cycles.
- Evidence eligibility tests for candidate, rejected, and superseded facts.
- Readiness assessment tests that keep evidence status unchanged when prerequisites block.
- Remediation ordering and deduplication tests.
- Citation-authorisation tests that reject uncited or ineligible claims.
- Workflow-node tests using fake AI, storage, and repository services.
- LangGraph interruption, checkpoint, and resume tests.
- API contract tests for validation, authorization, progress, review, and exports.
- Persistence integration tests, including transaction, tenancy, retention, and deletion behavior.
- Frontend tests for review state, status distinctions, blockers, and approval controls.
- End-to-end trust-packet tests from synthetic inputs through approved export.
- Adversarial LLM-output tests for malformed structure, invented controls, prompt injection, and unsupported claims.

Every layer preserves:

```text
No eligible evidence means no supported buyer-facing claim.
```

Current tests cover Pydantic models, deterministic extraction, matching, policy, answer and deficit generation, the trust-packet pipeline, API contracts, and an in-memory persistence adapter. They do not verify a live Supabase project or any target workflow, graph, AI, upload, export, or authentication capability.

## 14. Implementation sequence

The recommended sequence is:

1. Complete and commit corrected domain semantics.
2. Add versioned control catalog and dependency graph.
3. Add dependency-aware control assessment.
4. Add deterministic remediation planning.
5. Define application service interfaces.
6. Define workflow state and legal transitions.
7. Build the workflow with fake services.
8. Add structured AI extraction and mapping.
9. Add bounded answer drafting.
10. Implement LangGraph orchestration.
11. Add checkpoint persistence.
12. Add fact-review and export-review interrupts.
13. Add Supabase business persistence.
14. Connect FastAPI workflow endpoints.
15. Connect the Next.js workflow UI.
16. Add tracing and evaluations.

Frameworks should be introduced only after domain boundaries are stable. This keeps policy behavior testable without infrastructure, prevents workflow state from becoming accidental business truth, and makes AI providers replaceable. The milestone-level delivery plan and acceptance criteria are maintained in [../ROADMAP.md](../ROADMAP.md).

## 15. Architectural invariants

1. No eligible evidence means no supported buyer-facing claim.
2. Only approved facts may authorize buyer-facing claims.
3. Evidence status, answer value, and readiness status remain separate.
4. Missing evidence produces an unknown answer, not non-applicability.
5. Non-applicability requires explicit control-scoped evidence.
6. The Technical State Map and control dependency graph remain separate.
7. Dependency edges are curated and never generated by an LLM.
8. The dependency graph is versioned, deterministic, validated, and acyclic.
9. LangGraph coordinates workflow steps but cannot override policy decisions.
10. LangChain, when used, remains an AI integration utility rather than the product's authority.
11. LangGraph checkpoints do not replace durable business records.
12. Generated answers may use only authorised facts and citations.
13. Buyer-facing exports require explicit approval.
14. The deterministic kernel remains testable without external services.

The canonical safety properties and change expectations are maintained in [invariants.md](invariants.md). The deterministic policy boundary is recorded in [ADR 0001](adr/0001-deterministic-policy-boundary.md).
