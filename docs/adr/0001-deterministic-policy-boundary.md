# ADR 0001: Deterministic policy boundary

- Status: Accepted (existing behavior)
- Date: 2026-07-11

## Context

Verilly drafts security and compliance questionnaire answers from incomplete documentation. Optimistic inference can create contractual and security risk. Future extraction or wording may become more sophisticated, but answer authorization must remain reviewable and reproducible.

## Decision

A deterministic policy gate alone authorizes buyer-facing claims. `SUPPORTED` and `PARTIAL` answers use only policy-cited facts; missing or ineligible evidence produces a `DEFICIT` refusal. Dependency readiness is evaluated separately and cannot manufacture evidence or override policy. Any future LLM output is advisory until deterministic validation accepts its structured inputs.

## Consequences

- False deficits are preferable to unsupported positive claims.
- Policy and negative-case tests are required before changing extraction, matching, dependencies, wording, or infrastructure.
- Graph integration may block readiness but cannot promote evidence status.
- The system is a review aid, not certification or automatic approval.
