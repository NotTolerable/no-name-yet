# Verilly

Verilly is an evidence-first Enterprise AI-Risk & Governance Pre-Flight Checker for early-stage B2B AI startups. It compares a startup's documented technical state with buyer security and AI-risk questions, then produces reviewable answers, citations, compliance deficits, and remediation tasks.

> No explicit evidence = no positive compliance claim.

Verilly is a pre-flight checker. It is not a compliance certification platform, legal adviser, auditor, or substitute for professional security and compliance review.

## Target Architecture

The following diagram describes Verilly's target architecture. It is a design direction, not a description of what is already implemented.

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

Pydantic defines and validates the domain contracts. The deterministic domain kernel remains the final authority for evidence eligibility, dependency readiness, citations, and buyer-facing claim authorization. LangGraph coordinates resumability, retries, progress reporting, and human-review pauses; it does not make policy decisions. The AI service layer may extract candidate facts, propose question-to-control mappings, and draft bounded wording. LangChain is optional and may be used narrowly for model abstraction, structured output, prompts, and middleware.

Supabase is intended to store durable business records and uploaded or generated files. LangGraph checkpoints execution state but must not replace those business records. LangSmith or OpenTelemetry may be introduced later for tracing and evaluation.

The current implementation is substantially smaller: it uses deterministic regex extraction and matching, a synchronous local pipeline, a demo FastAPI API, a Next.js review UI, optional Supabase PostgREST persistence, and an offline versioned control dependency-graph utility. The graph is not integrated into verification or readiness. The system does not yet include LangGraph, LangChain, LLM services, authentication, uploads, human-review workflows, export generation, Supabase Storage, or production observability.

For detailed component boundaries, workflows, data ownership, and design invariants, see [docs/architecture.md](docs/architecture.md).

## Problem

Enterprise questionnaires ask startups to make precise claims about controls such as tenant isolation, encryption, model training, prompt retention, audit logging, incident response, SOC 2, and HIPAA. Generic autofill tools can turn incomplete documentation into confident but unsupported claims, creating procurement, contractual, and security risk.

## Solution

Verilly runs a governed verification pipeline:

- strong direct evidence produces a `SUPPORTED` evidence status with citations;
- incomplete, weak, neutral, or conflicting evidence produces a qualified `PARTIAL` status with citations;
- missing evidence produces a `DEFICIT` refusal and a remediation task.

Evidence status is distinct from answer meaning: a documented negative answer can be supported. The deterministic policy gate—not an LLM—decides whether a buyer-facing claim is allowed. Unsupported claims never become positive answers.

## Current Architecture

```text
Sample technical docs
  -> document chunks
  -> rule-based fact extraction
  -> Technical State Map
  -> questionnaire parsing
  -> deterministic evidence matching
  -> policy gate
  -> supported/partial answer or deficit
  -> TrustPacket
  -> FastAPI JSON API
  -> Next.js review UI
  -> optional Supabase persistence
```

The core modules are separated by responsibility:

- `backend/core/fact_graph.py`: loads documents, chunks them, and extracts explicit facts.
- `backend/core/evidence_matcher.py`: ranks candidate facts using control/category, keyword, and risk-domain signals.
- `backend/core/dependency_graph.py`: loads and validates the versioned control graph and provides deterministic prerequisite queries; it is not yet part of verification.
- `backend/core/policy.py`: returns `SUPPORTED`, `PARTIAL`, or `DEFICIT` deterministically.
- `backend/core/answer_generator.py`: renders only policy-approved facts and citations.
- `backend/core/deficit_generator.py`: creates remediation tasks for deficits.
- `backend/core/trust_packet.py`: orchestrates the end-to-end local pipeline.
- `backend/database.py`: optionally saves and loads completed runs through Supabase PostgREST.
- `backend/main.py`: exposes the demo through FastAPI.
- `frontend/`: provides the Next.js demo and results UI.

## Tech Stack

- Python 3.11+ and FastAPI
- Pydantic
- pytest
- Next.js App Router
- React and TypeScript
- Tailwind CSS
- ESLint
- Supabase Postgres, optional

The MVP does not call OpenAI, Gemini, or another LLM.

## Run the Backend

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Useful endpoints:

- `GET /health`
- `GET /demo/docs`
- `GET /demo/questionnaire`
- `POST /runs/demo`
- `GET /runs/{run_id}` when persistence is configured
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

### Optional Supabase Persistence

Apply `supabase/migrations/001_initial_schema.sql` to a Supabase project, then configure these variables in the backend environment only:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-backend-only-service-role-key"
```

Never expose `SUPABASE_SERVICE_ROLE_KEY` through a `NEXT_PUBLIC_*` variable or commit it to the repository. Without both variables, the demo remains fully functional but does not save runs.

## Run the Frontend

Start the backend first. In another terminal, from the repository root:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

The frontend runs at `http://127.0.0.1:3000`. `frontend/.env.example` sets:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Use `/demo` and select **Run Pre-Flight Check** to call the FastAPI demo pipeline.

## Run Tests and Checks

Backend:

```bash
cd backend
source .venv/bin/activate
python -m pytest
```

Frontend:

```bash
cd frontend
npm install
npm run lint
npx tsc --noEmit
npm run build
```

Do not report a command as passing unless it was actually run.

## What Is Mocked

- Demo documents and questionnaire questions are synthetic constants in `backend/main.py`.
- Tests use synthetic documents only; no real customer data is included.
- Database tests use an in-memory test double rather than a live Supabase project.
- Fact extraction and answer wording are rule-based and deterministic.
- There are no real buyer integrations, file uploads, authentication flows, or LLM calls.

## Key Product Decisions

- **Evidence before prose:** raw documents become structured facts before answers are considered.
- **Deterministic policy boundary:** answer generation cannot bypass the policy decision.
- **Citations are mandatory:** supported and partial answers cite the source evidence used.
- **Deficits are useful output:** missing evidence creates a refusal plus an actionable remediation task.
- **High-risk claims fail closed:** SOC 2 and HIPAA require explicit matching evidence; related security facts are insufficient.
- **Human review remains necessary:** generated trust packets are review artifacts, not automatic procurement approval.
- **Persistence is optional:** the local pipeline works without Supabase and preserves the same policy behavior when persistence is enabled.

## What Would Improve With More Time

- Add secure document and questionnaire uploads.
- Add authentication, authorization, and Supabase Row Level Security before multi-user use.
- Add richer parsers for PDF, DOCX, and complex questionnaire spreadsheets.
- Add provenance views linking citations to exact pages and sections.
- Add policy and extraction evaluation datasets with broader negative-case coverage.
- Add transactional persistence for complete run snapshots.
- Introduce schema-constrained LLM extraction only after deterministic evaluation gates are established.
- Add trust-packet export formats such as Markdown, CSV, and PDF.

## Known Limitations

- The demo recognizes a narrow set of controls using keyword rules; it is not a general compliance engine.
- Confidence is rule-based and does not establish that a control is correctly implemented.
- The sample data is fake and intentionally small.
- Supabase persistence requires external setup and has not been validated against a production Supabase environment.
- Persistence writes use sequential PostgREST requests rather than a database transaction.
- No authentication, RLS, uploads, billing, vector search, enterprise integrations, or production secret-management workflow is included.
- The frontend stores the latest demo packet in browser session storage for the results page.
- Verilly does not provide legal advice, audit assurance, certification, or proof of regulatory compliance.
