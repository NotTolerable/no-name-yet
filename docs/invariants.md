# Invariants

These rules are product safety properties, not implementation preferences.

1. **No evidence, no positive claim.** Missing binary evidence is `DEFICIT + UNKNOWN`, with no citations or positive control assertion.
2. **Approved evidence only.** Only `APPROVED` facts may authorize a buyer-facing claim. Candidate, rejected, and superseded facts are ineligible.
3. **Cited evidence only.** Every factual statement in a `SUPPORTED` or `PARTIAL` answer comes from policy-cited approved facts.
4. **Evidence is not answer meaning.** `SUPPORTED`, `PARTIAL`, and `DEFICIT` describe evidence; `YES`, `NO`, `UNKNOWN`, and `NOT_APPLICABLE` describe binary answer value. A documented `NO` may be supported.
5. **Explicit question semantics.** Every question declares `BINARY` or `FREE_TEXT`. Binary questions declare which fact polarity maps to `YES`; missing metadata fails closed.
6. **Free text is not binary.** Free-text questions have no affirmative polarity and no binary answer value.
7. **Scoped non-applicability.** `NOT_APPLICABLE` requires approved, explicit evidence scoped to the same canonical control. Missing evidence and unrelated clauses cannot establish it.
8. **Fail closed on conflict.** Conflicting approved positive and negative evidence produces `PARTIAL + UNKNOWN`, not an unqualified answer.
9. **Traceable provenance.** Every cited fact resolves to a source chunk and document; stable identifiers do not change for identical inputs.
10. **Evidence is not readiness.** Direct evidence and answer value remain separate from dependency readiness (`READY`, `INCOMPLETE`, `BLOCKED`).
11. **Separate state and dependency models.** The organization-specific Technical State Map contains reviewed facts; the control dependency graph contains curated product knowledge. Facts are never graph nodes or edges.
12. **Dependencies do not create evidence.** Prerequisites may block readiness in future assessment, but the graph cannot authorize or strengthen a direct claim.
13. **Curated deterministic graph.** Dependency edges are human-curated, versioned, acyclic, and never generated or overridden by an LLM.
14. **Invalid graphs fail closed.** Unknown controls, invalid or duplicate identifiers and edges, self-dependencies, version mismatches, and cycles are configuration errors, not warnings.
15. **Deterministic graph operations.** Identical catalogs, graph versions, and query inputs produce identical traversal and topological ordering results.
16. **Assurance requires evidence.** `soc2_status` cannot be inferred solely from technical dependency completion.
17. **Policy boundary.** Wording, infrastructure, persistence, dependency data, or future model output cannot override deterministic policy.
18. **Review artifact only.** Outputs never imply certification, legal advice, audit assurance, production compliance, or automatic procurement approval.

Changing these invariants requires explicit product review, documentation updates, and negative-case regression tests.
