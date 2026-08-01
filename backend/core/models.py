"""Pydantic data models for the Verilly verification pipeline."""

from enum import StrEnum

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


CONTROL_ID_PATTERN = r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$"
CATALOG_VERSION_PATTERN = r"^\d+\.\d+\.\d+$"


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


class DependencyType(StrEnum):
    """How a prerequisite affects a dependent control in future assessment."""

    REQUIRED = "REQUIRED"
    SUPPORTING = "SUPPORTING"


class _GraphModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class ControlDefinition(_GraphModel):
    id: str = Field(pattern=CONTROL_ID_PATTERN)
    name: str = Field(min_length=1)
    domain: str = Field(pattern=CONTROL_ID_PATTERN)
    description: str = Field(min_length=1)
    catalog_version: str = Field(pattern=CATALOG_VERSION_PATTERN)


class ControlDependency(_GraphModel):
    """A directed prerequisite: control_id depends on depends_on_control_id."""

    control_id: str = Field(pattern=CONTROL_ID_PATTERN)
    depends_on_control_id: str = Field(pattern=CONTROL_ID_PATTERN)
    dependency_type: DependencyType
    reason: str = Field(min_length=1)


class ControlCatalog(_GraphModel):
    catalog_version: str = Field(pattern=CATALOG_VERSION_PATTERN)
    controls: tuple[ControlDefinition, ...]

    @model_validator(mode="after")
    def validate_catalog_consistency(self) -> "ControlCatalog":
        control_ids = [control.id for control in self.controls]
        duplicate_ids = sorted(
            control_id
            for control_id in set(control_ids)
            if control_ids.count(control_id) > 1
        )
        if duplicate_ids:
            raise ValueError(
                "Duplicate control IDs: " + ", ".join(duplicate_ids)
            )

        mismatched_ids = sorted(
            control.id
            for control in self.controls
            if control.catalog_version != self.catalog_version
        )
        if mismatched_ids:
            raise ValueError(
                "Control catalog versions do not match catalog_version for: "
                + ", ".join(mismatched_ids)
            )
        return self


class ControlDependencySet(_GraphModel):
    catalog_version: str = Field(pattern=CATALOG_VERSION_PATTERN)
    dependencies: tuple[ControlDependency, ...]


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

