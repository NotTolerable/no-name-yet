# Domain model

## Current entities

| Entity | Meaning | Key relationships |
|---|---|---|
| `Document` | Raw local text source | Owns ordered `DocumentChunk`s |
| `DocumentChunk` | Traceable blank-line section | References one document |
| `Fact` | Documented proposition | References one chunk; has category, confidence, polarity, review status, and applicability |
| `Question` | Buyer requirement | Names a control, response kind, and explicit binary orientation when applicable |
| `EvidenceMatch` | Ranked candidate link | Joins one question to one approved fact |
| `PolicyDecision` | Internal direct-evidence assessment | Evidence status, answer value, response kind, cited fact IDs, and reason |
| `Answer` | Buyer-facing rendering | Retains the external `status`, text, citations, and policy reason contract |
| `RemediationTask` | Follow-up for a deficit | One question; title, description, severity, owner |
| `TrustPacket` | Current run result | Answers, tasks, summary only |

## Domain values

- `EvidenceStatus`: `SUPPORTED`, `PARTIAL`, `DEFICIT` describes evidence quality, not whether an answer is affirmative.
- `AnswerValue`: `YES`, `NO`, `UNKNOWN`, `NOT_APPLICABLE` describes a binary answer's meaning.
- `ReadinessStatus`: `READY`, `INCOMPLETE`, `BLOCKED` is reserved for future dependency assessment and is not part of policy or answers yet.
- `FactPolarity`: `POSITIVE`, `NEGATIVE`, `NEUTRAL` is relative to the canonical proposition represented by the fact category.
- `FactReviewStatus`: `CANDIDATE`, `APPROVED`, `REJECTED`, `SUPERSEDED` governs authorization. Only approved facts are usable.
- `FactApplicability`: `APPLICABLE`, `NOT_APPLICABLE`, `UNSPECIFIED` records explicit control-scoped applicability.
- `QuestionResponseKind`: `BINARY`, `FREE_TEXT` is required on every question.

Binary questions require `affirmative_polarity` (`POSITIVE` or `NEGATIVE`), which declares which fact polarity maps to `YES`. Free-text questions require `affirmative_polarity=None` and their policy decision has `answer_value=None`. Missing metadata fails validation; wording is never used to guess question kind or orientation.

## Policy semantics

- The trusted deterministic extractor explicitly emits `APPROVED`; future untrusted extractors must not inherit approval.
- Candidate, rejected, and superseded facts cannot match, support policy, or reach buyer-facing wording.
- Approved negative evidence may produce `SUPPORTED + NO`.
- Missing binary evidence produces `DEFICIT + UNKNOWN` without citations.
- Conflicting approved positive and negative evidence produces `PARTIAL + UNKNOWN`.
- `NOT_APPLICABLE` requires an approved fact whose canonical category matches the question and whose typed applicability is explicitly `NOT_APPLICABLE`.
- Evidence status and answer value remain separate from future readiness.

`PolicyStatus` remains a temporary alias for `EvidenceStatus`, and external `Answer.status` is unchanged. Answer value is intentionally not persisted or exposed in the current TrustPacket.

## Known gaps

- No canonical control catalog, dependency graph, or control assessment exists yet.
- Fact applicability and review status are not persisted; current runs reconstruct facts through the deterministic extractor.
- Evidence matches and policy decisions are transient and absent from TrustPacket persistence.
- API citations are quote strings rather than first-class provenance objects.
- No first-class Technical State Map aggregate exists.
- Remediation remains question-oriented.
- Confidence is fixed rule output rather than calibrated evidence quality.
