from core.models import (
    Answer,
    Document,
    DocumentChunk,
    EvidenceMatch,
    Fact,
    PolicyDecision,
    PolicyStatus,
    Question,
    RemediationTask,
    TrustPacket,
)


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
    )
    question = Question(
        id="q-1",
        question_text="Where is customer data stored?",
        required_control="data_storage_location",
        risk_domain="security",
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
        reason="Direct evidence exists.",
        cited_fact_ids=["fact-1"],
    )
    partial = PolicyDecision(
        question_id="q-partial",
        status="PARTIAL",
        reason="Evidence covers only part of the requested control.",
        cited_fact_ids=["fact-2"],
    )
    deficit = PolicyDecision(
        question_id="q-deficit",
        status="DEFICIT",
        reason="No explicit evidence exists.",
        cited_fact_ids=[],
    )

    assert supported.status is PolicyStatus.SUPPORTED
    assert partial.status is PolicyStatus.PARTIAL
    assert deficit.status is PolicyStatus.DEFICIT

