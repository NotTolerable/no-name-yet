from core.models import (
    Answer,
    AnswerValue,
    Document,
    DocumentChunk,
    EvidenceStatus,
    EvidenceMatch,
    Fact,
    FactApplicability,
    FactPolarity,
    FactReviewStatus,
    PolicyDecision,
    PolicyStatus,
    Question,
    QuestionResponseKind,
    ReadinessStatus,
    RemediationTask,
    TrustPacket,
)
import pytest
from pydantic import ValidationError


def test_pipeline_models_can_be_created_and_serialized():
    document = Document(
        id="doc-1",
        file_name="architecture.md",
        text="All customer data is stored in a managed Postgres database.",
    )
    chunk = DocumentChunk(
        id="chunk-1",
        document_id=document.id,
        chunk_index=0,
        text=document.text,
        source_label="architecture.md#chunk-0",
    )
    fact = Fact(
        id="fact-1",
        category="data_storage",
        claim="Customer data is stored in managed Postgres.",
        evidence_quote="All customer data is stored in a managed Postgres database.",
        source_document=document.file_name,
        source_chunk_id=chunk.id,
        confidence=0.95,
        polarity=FactPolarity.NEUTRAL,
        review_status=FactReviewStatus.APPROVED,
        applicability=FactApplicability.UNSPECIFIED,
    )
    question = Question(
        id="q-1",
        question_text="Where is customer data stored?",
        required_control="data_storage_location",
        risk_domain="security",
        response_kind=QuestionResponseKind.FREE_TEXT,
        affirmative_polarity=None,
    )
    evidence_match = EvidenceMatch(
        question_id=question.id,
        fact_id=fact.id,
        relevance=0.9,
        reason="The fact directly identifies the storage system.",
    )
    decision = PolicyDecision(
        question_id=question.id,
        status=PolicyStatus.SUPPORTED,
        answer_value=None,
        response_kind=QuestionResponseKind.FREE_TEXT,
        reason="Direct evidence exists in the architecture document.",
        cited_fact_ids=[fact.id],
    )
    answer = Answer(
        question_id=question.id,
        status=decision.status,
        answer_text="Customer data is stored in managed Postgres.",
        citations=[fact.evidence_quote],
        policy_reason=decision.reason,
    )
    remediation_task = RemediationTask(
        question_id="q-2",
        title="Document audit logging",
        description="Add technical documentation describing audit log coverage and retention.",
        severity="medium",
        suggested_owner="engineering",
    )
    trust_packet = TrustPacket(
        answers=[answer],
        remediation_tasks=[remediation_task],
        summary="One supported answer and one remediation task are ready for review.",
    )

    serialized = trust_packet.model_dump()

    assert evidence_match.model_dump()["question_id"] == question.id
    assert serialized["answers"][0]["status"] == "SUPPORTED"
    assert serialized["answers"][0]["citations"] == [fact.evidence_quote]
    assert serialized["remediation_tasks"][0]["question_id"] == "q-2"


def test_policy_status_accepts_required_values():
    supported = PolicyDecision(
        question_id="q-supported",
        status="SUPPORTED",
        answer_value="YES",
        response_kind=QuestionResponseKind.BINARY,
        reason="Direct evidence exists.",
        cited_fact_ids=["fact-1"],
    )
    partial = PolicyDecision(
        question_id="q-partial",
        status="PARTIAL",
        answer_value="NO",
        response_kind=QuestionResponseKind.BINARY,
        reason="Evidence covers only part of the requested control.",
        cited_fact_ids=["fact-2"],
    )
    deficit = PolicyDecision(
        question_id="q-deficit",
        status="DEFICIT",
        answer_value="UNKNOWN",
        response_kind=QuestionResponseKind.BINARY,
        reason="No explicit evidence exists.",
        cited_fact_ids=[],
    )

    assert supported.status is PolicyStatus.SUPPORTED
    assert partial.status is PolicyStatus.PARTIAL
    assert deficit.status is PolicyStatus.DEFICIT


def test_domain_enums_are_separate():
    assert EvidenceStatus.SUPPORTED.value == "SUPPORTED"
    assert AnswerValue.NO.value == "NO"
    assert ReadinessStatus.BLOCKED.value == "BLOCKED"
    assert FactPolarity.NEUTRAL.value == "NEUTRAL"
    assert FactReviewStatus.SUPERSEDED.value == "SUPERSEDED"
    assert FactApplicability.NOT_APPLICABLE.value == "NOT_APPLICABLE"
    assert QuestionResponseKind.FREE_TEXT.value == "FREE_TEXT"


def test_supported_negative_binary_decision():
    decision = PolicyDecision(
        question_id="q-soc2",
        evidence_status=EvidenceStatus.SUPPORTED,
        answer_value=AnswerValue.NO,
        response_kind=QuestionResponseKind.BINARY,
        reason="Approved explicit evidence documents a negative answer.",
        cited_fact_ids=["fact-soc2-negative"],
    )

    assert decision.evidence_status is EvidenceStatus.SUPPORTED
    assert decision.answer_value is AnswerValue.NO


def test_free_text_decision_permits_null_answer_value():
    decision = PolicyDecision(
        question_id="q-storage",
        evidence_status=EvidenceStatus.SUPPORTED,
        answer_value=None,
        response_kind=QuestionResponseKind.FREE_TEXT,
        reason="Approved evidence provides the requested description.",
        cited_fact_ids=["fact-storage"],
    )

    assert decision.answer_value is None


def test_binary_decision_requires_answer_value():
    with pytest.raises(ValidationError, match="Binary decisions require"):
        PolicyDecision(
            question_id="q-invalid",
            evidence_status=EvidenceStatus.SUPPORTED,
            answer_value=None,
            response_kind=QuestionResponseKind.BINARY,
            reason="Invalid binary decision.",
            cited_fact_ids=["fact-1"],
        )


def test_missing_evidence_cannot_be_not_applicable():
    with pytest.raises(ValidationError, match="Deficit decisions must use"):
        PolicyDecision(
            question_id="q-invalid-na",
            evidence_status=EvidenceStatus.DEFICIT,
            answer_value=AnswerValue.NOT_APPLICABLE,
            response_kind=QuestionResponseKind.BINARY,
            reason="No evidence exists.",
            cited_fact_ids=[],
        )


def test_legacy_status_input_and_property_remain_compatible():
    decision = PolicyDecision(
        question_id="q-legacy",
        status="SUPPORTED",
        answer_value="YES",
        response_kind=QuestionResponseKind.BINARY,
        reason="Approved explicit evidence exists.",
        cited_fact_ids=["fact-1"],
    )

    assert decision.status is EvidenceStatus.SUPPORTED
    assert decision.model_dump()["evidence_status"] == "SUPPORTED"


def test_question_requires_explicit_response_kind():
    with pytest.raises(ValidationError, match="response_kind"):
        Question(
            id="q-missing-kind",
            question_text="Is encryption at rest enabled?",
            required_control="encryption_at_rest",
            risk_domain="security",
            affirmative_polarity=FactPolarity.POSITIVE,
        )


def test_binary_question_requires_explicit_affirmative_polarity():
    with pytest.raises(ValidationError, match="affirmative_polarity"):
        Question(
            id="q-missing-orientation",
            question_text="Is encryption at rest enabled?",
            required_control="encryption_at_rest",
            risk_domain="security",
            response_kind=QuestionResponseKind.BINARY,
        )


def test_free_text_question_rejects_affirmative_polarity():
    with pytest.raises(ValidationError, match="cannot define affirmative_polarity"):
        Question(
            id="q-invalid-free-text",
            question_text="Where is customer data stored?",
            required_control="data_storage_location",
            risk_domain="security",
            response_kind=QuestionResponseKind.FREE_TEXT,
            affirmative_polarity=FactPolarity.POSITIVE,
        )


def test_binary_orientation_survives_normal_serialization():
    question = Question(
        id="q-negative-orientation",
        question_text="Do you avoid retaining prompts?",
        required_control="prompt_retention",
        risk_domain="ai_governance",
        response_kind=QuestionResponseKind.BINARY,
        affirmative_polarity=FactPolarity.NEGATIVE,
    )

    serialized = question.model_dump(mode="json")
    restored = Question.model_validate(serialized)

    assert serialized["response_kind"] == "BINARY"
    assert serialized["affirmative_polarity"] == "NEGATIVE"
    assert restored == question

