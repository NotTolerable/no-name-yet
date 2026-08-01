# Product

## Goal

Verilly helps early-stage B2B AI companies review enterprise security and AI-governance questionnaire answers against explicit technical documentation. It favors traceability and safe refusal over completion rate.

## Current behavior

- Inputs are local `.md`/`.txt` documents and JSON/CSV questions; the public demo uses synthetic constants.
- Narrow regex rules extract facts for a small set of controls.
- Heuristics match questions to facts; a deterministic policy gate returns `SUPPORTED`, `PARTIAL`, or `DEFICIT`.
- Supported and partial answers contain policy-cited source quotations. Deficits use fixed refusal text and create remediation tasks.
- A `TrustPacket` contains answers, remediation tasks, and a count summary.
- FastAPI serves demo runs; Next.js displays results. Supabase storage is optional and unverified against a live project.
- A versioned control catalog and offline dependency-graph utility exist, but current application behavior does not invoke them. There is no readiness assessment or dependency-aware remediation.

## Current boundaries

Verilly is not a questionnaire autofill service, control implementation verifier, certification platform, auditor, legal adviser, or production-ready multi-tenant service. It has no authentication, uploads, RLS, buyer integrations, transactional run persistence, or LLM calls.

## Target direction

The next product step is a dependency-aware verification kernel: map questionnaire controls to one canonical catalog, assess direct evidence separately from prerequisite readiness, and expose ordered, traceable remediation without weakening answer policy. Broader ingestion, collaboration, and production hardening follow only after this kernel is coherent and tested.

## Success criteria

- Reviewers can trace every positive claim to explicit source evidence.
- Missing or ambiguous evidence fails closed.
- A supported control can still be visibly blocked by unmet required prerequisites.
- Remediation identifies and orders prerequisites without duplicates.
- Re-running identical inputs and catalog versions produces identical results.
