# AGENTS.md

## Project Goal

Verilly is an Enterprise AI-Risk & Governance Pre-Flight Checker for early-stage B2B AI startups.

The product helps teams answer enterprise AI-risk, security, privacy, and governance questionnaires safely by reading the startup's actual technical documentation, extracting verifiable facts, and generating buyer-facing answers only when those answers are supported by explicit source evidence.

Core product rule:

> No explicit evidence = no positive compliance claim.

Verilly must behave like a governed verification pipeline, not a generic questionnaire autofill bot.

## Product Scope

Verilly should support a narrow, evidence-first workflow:

1. Ingest startup-provided technical and policy documentation.
2. Split raw documents into traceable document chunks.
3. Extract structured facts from those chunks.
4. Build a Technical State Map representing what is actually documented.
5. Parse buyer questionnaire requirements.
6. Match requirements against extracted evidence.
7. Apply policy gates before drafting any buyer-facing answer.
8. Generate one of:
   - a supported answer with citation,
   - a qualified `PARTIAL` answer,
   - a `DEFICIT` refusal with remediation tasks.
9. Export a trust packet containing answers, citations, deficits, and supporting evidence.

The first version should prioritize correctness, traceability, and refusal behavior over breadth or automation.

## Non-Goals

Do not build a generic questionnaire autofill bot.

Do not create unsupported claims about:

- SOC 2
- HIPAA
- encryption
- access control
- audit logging
- data retention
- PII scrubbing
- model training
- security monitoring
- incident response
- regulatory compliance

Do not add these features unless explicitly requested later:

- authentication
- payment or billing
- trust-center hosting
- enterprise integrations
- real customer data processing
- production compliance claims
- broad workflow automation
- unrelated governance frameworks

Do not overbuild. Prefer a small, auditable system with clear policy boundaries.

## Architecture

The intended pipeline is:

```text
Raw docs
  -> document chunks
  -> fact extraction
  -> Technical State Map
  -> questionnaire parsing
  -> evidence matching
  -> policy gate
  -> answer or compliance deficit
  -> trust packet export
```

Each stage should preserve enough metadata for traceability:

- source document ID
- source filename
- chunk ID
- page, section, or location when available
- extracted fact IDs
- questionnaire item IDs
- evidence match IDs
- policy decision result

The policy gate is a first-class system boundary. Buyer-facing text must not bypass it.

## Tech Stack

Planned stack:

- Python for core logic
- FastAPI for backend APIs
- Pydantic for backend schemas and validation
- pytest for backend and pipeline tests
- Supabase Postgres for relational storage
- Supabase Storage for uploaded source documents and exported trust packets
- Next.js for frontend
- TypeScript for frontend code
- OpenAI or Gemini for structured extraction and answer drafting

Use the smallest practical subset of the stack until implementation requirements justify more.

## Folder Structure

Expected project shape once implementation begins:

```text
.
├── AGENTS.md
├── README.md
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── policies/
│   └── tests/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── tests/
├── docs/
│   ├── product/
│   ├── architecture/
│   └── examples/
└── supabase/
    ├── migrations/
    └── seed/
```

Do not create this structure until implementation work begins. For now, this repository may contain only planning and documentation files.

## Core Policy Rules

These rules are mandatory and should be encoded in tests when implementation begins:

1. If direct evidence exists, generate a supported answer with citation.
2. If evidence is partial, generate a qualified answer marked `PARTIAL`.
3. If evidence is missing, refuse to answer and mark `DEFICIT`.
4. Never invent SOC 2, HIPAA, encryption, access control, audit logging, data retention, PII scrubbing, or model-training claims.
5. Buyer-facing answers must cite source evidence.
6. Deficits must generate remediation tasks.
7. The system must distinguish between:
   - documented fact,
   - inferred possibility,
   - unsupported claim,
   - remediation recommendation.
8. Unsupported claims must not appear in buyer-facing answer text.
9. LLM output is advisory until validated by deterministic policy checks.
10. Every generated answer must retain a machine-readable policy decision.

Recommended policy decision states:

- `SUPPORTED`
- `PARTIAL`
- `DEFICIT`
- `NOT_APPLICABLE`
- `NEEDS_REVIEW`

## Testing Strategy

Tests should focus on evidence handling and refusal behavior before UI polish.

Backend and pipeline tests should cover:

- document chunk traceability
- fact extraction schema validation
- questionnaire requirement parsing
- evidence matching behavior
- policy gate decisions
- supported answer generation with citations
- partial answer qualification
- deficit refusal behavior
- remediation task generation
- prevention of unsupported compliance claims

Use fixture documents with synthetic data only. Do not use real customer data.

Minimum expected test types:

- unit tests for pure policy functions
- schema validation tests for Pydantic models
- integration tests for pipeline stages
- regression tests for high-risk compliance claims
- frontend tests for rendering decision states and citations once UI exists

## Backend Rules

Backend code should keep policy, extraction, matching, and drafting concerns separate.

Guidelines:

- Use Pydantic models for request, response, and internal pipeline schemas.
- Treat uploaded documents as untrusted input.
- Store source references for every extracted fact.
- Keep policy decisions deterministic where possible.
- Keep LLM prompts and model adapters behind explicit service boundaries.
- Do not let raw LLM responses directly become buyer-facing answers.
- Validate all generated structured output before use.
- Prefer explicit enums for decision states, evidence strength, and claim categories.
- Avoid hidden global state in pipeline code.
- Keep API routes thin; put business logic in services or core modules.

## Frontend Rules

The frontend should make evidence status obvious.

Guidelines:

- Show questionnaire items with their policy decision state.
- Clearly distinguish `SUPPORTED`, `PARTIAL`, and `DEFICIT`.
- Surface citations near buyer-facing answers.
- Show remediation tasks for deficits.
- Avoid UI language that implies production compliance.
- Do not hide unsupported status behind optimistic wording.
- Use TypeScript types that mirror backend response models.
- Prefer simple, inspectable workflows over dashboards with decorative complexity.

The first UI should support review and verification, not broad enterprise workflow management.

## AI/LLM Usage Rules

LLMs may be used for:

- structured fact extraction
- questionnaire requirement parsing
- evidence candidate ranking
- draft answer wording
- remediation task drafting

LLMs must not be the final authority on:

- whether a claim is supported
- whether evidence is sufficient
- whether a company is compliant
- whether a buyer-facing answer may include a positive compliance claim

Rules:

- Always validate structured LLM output against schemas.
- Keep source citations attached to generated claims.
- Do not allow claims without evidence references.
- Prefer conservative wording.
- Refuse or mark `DEFICIT` when evidence is missing.
- Mark uncertainty explicitly.
- Do not train on or retain customer documents outside the configured provider and storage policies.
- Keep prompts versioned once implementation begins.

## Security and Privacy Assumptions

Early versions are not production compliant.

Assumptions:

- Use synthetic, sample, or user-approved test documents only.
- Do not use real customer data during development.
- Treat all uploaded files as confidential and untrusted.
- Do not expose documents, extracted facts, answers, or trust packets publicly.
- Do not claim SOC 2, HIPAA, GDPR, or other compliance certification for Verilly.
- Do not add authentication until explicitly requested.
- Do not add payment, billing, or enterprise integrations until explicitly requested.
- Keep secrets out of the repository.
- Use environment variables for provider keys and database credentials when implementation begins.

## Documentation References

Future documentation should live under `docs/` once implementation begins.

Recommended references:

- `docs/product/product-requirements.md`
- `docs/architecture/pipeline.md`
- `docs/architecture/policy-gate.md`
- `docs/examples/sample-questionnaires.md`
- `docs/examples/sample-technical-docs.md`
- `docs/examples/trust-packet-format.md`

Documentation must preserve the central product rule:

> No explicit evidence = no positive compliance claim.

## Verification Commands

No implementation exists yet, so there are no required build or test commands.

Once implementation begins, expected commands should be documented here and in `README.md`.

Likely future commands:

```bash
pytest
npm test
npm run lint
npm run typecheck
```

Before merging implementation work, run the commands relevant to the changed files and report any command that could not be run.

## README Expectations

`README.md` should eventually explain:

- what Verilly does
- the evidence-first product rule
- what the project does not claim
- local setup instructions
- required environment variables
- how to run backend tests
- how to run frontend checks
- how to use sample documents and questionnaires
- how policy decisions are represented
- how trust packet export works

The README must not imply that Verilly provides legal advice, security certification, production compliance, or automated approval for enterprise procurement.
