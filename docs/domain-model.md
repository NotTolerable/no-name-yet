# Domain model

## Current entities

| Entity | Meaning | Key relationships |
|---|---|---|
| `Document` | Raw local text source | Owns ordered `DocumentChunk`s |
| `DocumentChunk` | Traceable blank-line section | References one document |
| `Fact` | Regex-detected documented statement | References one chunk; carries quote, category, confidence |
| `Question` | Buyer requirement | Names a free-form required control and risk domain |
| `EvidenceMatch` | Ranked candidate link | Joins one question to one fact |
| `PolicyDecision` | Direct-evidence authorization | One question; status and cited fact IDs |
| `Answer` | Buyer-facing rendering | One question; policy status, text, quote citations |
| `RemediationTask` | Follow-up for a deficit | One question; optional control and blocker IDs |
| `TrustPacket` | Current run result | Answers, tasks, summary only |
| `ControlDefinition` | Canonical catalog entry | Identified by control ID |
| `ControlDependency` | Directed prerequisite edge | Control depends on another control; required or supporting |
| `ControlAssessment` | Evidence plus readiness result | One control; cited facts and missing required dependencies |

`PolicyStatus` is currently reused as `ControlAssessment.evidence_status`. `ReadinessStatus` is independently `READY`, `INCOMPLETE`, or `BLOCKED`.

## Relationship rules

- A fact belongs to exactly one source chunk; a chunk belongs to one document.
- An evidence match never itself authorizes an answer.
- A policy decision may cite facts; answer generation accepts only those cited facts.
- A control dependency points from the dependent control to its prerequisite.
- Only required dependencies block readiness.
- Graph utilities and questionnaire processing currently form separate models.

## Known modeling gaps

- No explicit `Run` or verification-result model exists in core; persistence adds run identity externally.
- No canonical mapping connects free-form question/fact labels to catalog control IDs.
- No first-class Technical State Map aggregate exists despite the architectural name.
- Evidence matches and policy decisions are transient and absent from `TrustPacket` and persistence.
- API citations are strings rather than citation objects containing fact/chunk/document IDs.
- Graph/catalog version is loaded but discarded from domain results.
- Control assessments are not computed as a complete, topologically evaluated set.
- Remediation identity is ambiguous between question and control; persistence enforces question uniqueness.
- There is no representation for conflicting, stale, superseded, or negatively asserted facts.
- Confidence is a fixed extraction value in current behavior, not calibrated evidence quality.

The next milestone should close only the gaps required for dependency-aware verification; it should not broaden ingestion or compliance scope.

