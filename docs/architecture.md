# Architecture

## Current architecture

```text
.md/.txt docs -> chunks -> regex facts -------------------+
                                                        |
JSON/CSV questions -> heuristic evidence matches -> policy gate
                                                        |
                         cited answer or deficit -> remediation
                                                        |
                                                  TrustPacket
                                                        |
                           FastAPI -> Next.js / optional Supabase

versioned control catalog + dependency JSON -> graph utilities
                                              (not orchestrated above)
```

Backend responsibilities:

- `fact_graph.py`: deterministic loading, chunking, fact extraction, and stable source IDs.
- `evidence_matcher.py`: category, keyword, and risk-domain candidate ranking.
- `policy.py`: explicit-evidence gate and evidence status.
- `answer_generator.py`: renders only cited facts; refuses deficits.
- `deficit_generator.py`: creates deficit tasks; dependency metadata is optional and unused by the main pipeline.
- `dependency_graph.py`: loads and validates curated graph data, resolves prerequisites, derives readiness, and orders control IDs.
- `trust_packet.py`: current end-to-end orchestration; it does not call the dependency graph.
- `main.py`: synthetic demo API and optional persistence orchestration.
- `database.py`: sequential PostgREST persistence behind a small protocol.

The frontend calls the demo API from the browser and keeps the latest packet in session storage. It does not render control assessments or dependency blockers.

## Target architecture

```text
facts + questions -> canonical control mapping -> direct evidence decisions
                                                   |
versioned validated dependency graph --------------+
                                                   v
                                      control assessments
                              (evidence status != readiness)
                                                   |
                              policy-safe answers + ordered remediation
                                                   |
                              versioned, traceable verification result
```

The target remains deterministic. The graph is curated data, validated at startup or pipeline entry, and pinned by version in results. Dependency readiness may qualify readiness/remediation, but must never manufacture direct evidence or authorize buyer-facing claims.

## Contradictions and risks

- Product naming is split: requested documentation says Proofline; package names, API title, storage key, README, and UI say Verilly.
- The graph models use `PolicyStatus` as evidence status, coupling questionnaire policy vocabulary to control assessment.
- Question/fact control labels (`tenant_isolation`, `audit_logging`, `soc2_type_ii`) differ from catalog IDs (`tenant_data_scoping`, `centralized_audit_logging`, `soc2_status`); no canonical mapping exists.
- Graph assessment depends on caller-supplied prerequisite assessments and has no full-graph evaluation orchestration.
- `TrustPacket`, API, frontend types, and persistence omit control assessments and graph version.
- Persistence omits `control_id` and `blocked_by_control_ids`; its schema allows only one remediation task per question, while dependency remediation is naturally control-oriented.
- Citations in API results are quotation strings, while policy decisions use fact IDs; persisted answers reconstruct links by matching quote text, which can be ambiguous.
- The so-called Technical State Map is an in-memory list of facts, not an explicit aggregate or returned artifact.
- Dependencies use unpinned `latest` versions in the frontend, reducing build reproducibility.
- Browser session storage is a demo convenience, not a durable review workflow.

