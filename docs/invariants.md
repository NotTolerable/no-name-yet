# Invariants

These rules are product safety properties, not implementation preferences.

1. **No evidence, no positive claim.** `DEFICIT` answers contain no positive compliance or control assertion and no citations.
2. **Cited evidence only.** Every factual statement in a `SUPPORTED` or `PARTIAL` answer comes from facts explicitly cited by the policy decision.
3. **Traceable provenance.** Every cited fact resolves to a source chunk and document; identifiers remain stable for identical inputs.
4. **Fail closed.** Missing, ambiguous, conflicting, ineligible, or untraceable evidence cannot produce a stronger result.
5. **Evidence is not readiness.** Direct evidence status (`SUPPORTED`, `PARTIAL`, `DEFICIT`) and dependency readiness (`READY`, `INCOMPLETE`, `BLOCKED`) remain separate.
6. **Dependencies do not create evidence.** A ready prerequisite cannot support a dependent control's direct claim. A supported dependent control may still be blocked.
7. **Curated deterministic graph.** Control definitions and edges are human-curated, versioned, deterministic, and validated; no LLM creates or overrides edges.
8. **Acyclic valid graph.** Unknown controls, self-edges, duplicate edges, and cycles are rejected before assessment.
9. **Required versus supporting.** Missing required dependencies can block readiness. Supporting dependencies can explain risk but cannot automatically block it.
10. **Deterministic remediation.** Prerequisite tasks precede dependent tasks, and at most one task exists per control in a result.
11. **Policy boundary.** Wording, infrastructure, persistence, or future model output cannot override deterministic policy.
12. **Review artifact only.** Outputs never imply certification, legal advice, audit assurance, production compliance, or automatic procurement approval.

Any change to these invariants requires explicit product review, an ADR update or replacement, and negative-case regression tests.

