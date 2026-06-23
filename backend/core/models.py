"""Pydantic data models for the Verilly verification pipeline."""

from enum import StrEnum

from pydantic import BaseModel, Field


class PolicyStatus(StrEnum):
    """Allowed policy gate outcomes for buyer-facing answers."""

    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    DEFICIT = "DEFICIT"


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


class Question(BaseModel):
    id: str
    question_text: str
    required_control: str
    risk_domain: str


class EvidenceMatch(BaseModel):
    question_id: str
    fact_id: str
    relevance: float = Field(ge=0.0, le=1.0)
    reason: str


class PolicyDecision(BaseModel):
    question_id: str
    status: PolicyStatus
    reason: str
    cited_fact_ids: list[str]


class Answer(BaseModel):
    question_id: str
    status: PolicyStatus
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

