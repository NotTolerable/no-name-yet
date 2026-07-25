"""Pydantic data models for the Verilly verification pipeline."""

from enum import StrEnum

from pydantic import AliasChoices, BaseModel, Field, model_validator


class EvidenceStatus(StrEnum):
    """Quality and sufficiency of evidence for an answer."""

    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    DEFICIT = "DEFICIT"


PolicyStatus = EvidenceStatus
"""Temporary compatibility alias for the former evidence-status name."""


class AnswerValue(StrEnum):
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ReadinessStatus(StrEnum):
    READY = "READY"
    INCOMPLETE = "INCOMPLETE"
    BLOCKED = "BLOCKED"


class FactPolarity(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class FactReviewStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class FactApplicability(StrEnum):
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNSPECIFIED = "UNSPECIFIED"


class QuestionResponseKind(StrEnum):
    BINARY = "BINARY"
    FREE_TEXT = "FREE_TEXT"


class Document(BaseModel):
    id: str
    file_name: str
    text: str


class DocumentChunk(BaseModel):
    id: str
    document_id: str
    chunk_index: int = Field(ge=0)
    text: str
    source_label: str


class Fact(BaseModel):
    id: str
    category: str
    claim: str
    evidence_quote: str
    source_document: str
    source_chunk_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    polarity: FactPolarity
    review_status: FactReviewStatus
    applicability: FactApplicability


class Question(BaseModel):
    id: str
    question_text: str
    required_control: str
    risk_domain: str
    response_kind: QuestionResponseKind
    affirmative_polarity: FactPolarity | None

    @model_validator(mode="after")
    def validate_response_semantics(self) -> "Question":
        if self.response_kind is QuestionResponseKind.BINARY:
            if self.affirmative_polarity not in {
                FactPolarity.POSITIVE,
                FactPolarity.NEGATIVE,
            }:
                raise ValueError(
                    "Binary questions require POSITIVE or NEGATIVE affirmative_polarity"
                )
        elif self.affirmative_polarity is not None:
            raise ValueError("Free-text questions cannot define affirmative_polarity")
        return self


class EvidenceMatch(BaseModel):
    question_id: str
    fact_id: str
    relevance: float = Field(ge=0.0, le=1.0)
    reason: str


class PolicyDecision(BaseModel):
    question_id: str
    evidence_status: EvidenceStatus = Field(
        validation_alias=AliasChoices("evidence_status", "status")
    )
    answer_value: AnswerValue | None
    response_kind: QuestionResponseKind
    reason: str
    cited_fact_ids: list[str]

    @model_validator(mode="after")
    def validate_decision_semantics(self) -> "PolicyDecision":
        if self.response_kind is QuestionResponseKind.BINARY:
            if self.answer_value is None:
                raise ValueError("Binary decisions require an answer value")
        elif self.answer_value is not None:
            raise ValueError("Free-text decisions must have a null answer value")

        if self.evidence_status is EvidenceStatus.DEFICIT:
            expected = (
                AnswerValue.UNKNOWN
                if self.response_kind is QuestionResponseKind.BINARY
                else None
            )
            if self.answer_value is not expected:
                raise ValueError("Deficit decisions must use the unknown answer value")
            if self.cited_fact_ids:
                raise ValueError("Deficit decisions cannot cite facts")
        elif not self.cited_fact_ids:
            raise ValueError("Supported and partial decisions require cited facts")

        if (
            self.answer_value is AnswerValue.NOT_APPLICABLE
            and not self.cited_fact_ids
        ):
            raise ValueError("Not-applicable answers require explicit cited evidence")
        return self

    @property
    def status(self) -> EvidenceStatus:
        """Deprecated compatibility view of ``evidence_status``."""

        return self.evidence_status


class Answer(BaseModel):
    question_id: str
    status: EvidenceStatus
    answer_text: str
    citations: list[str]
    policy_reason: str


class RemediationTask(BaseModel):
    question_id: str
    title: str
    description: str
    severity: str
    suggested_owner: str


class TrustPacket(BaseModel):
    answers: list[Answer]
    remediation_tasks: list[RemediationTask]
    summary: str

