import pytest

from core.models import Fact, PolicyStatus, Question
from core.policy import evaluate_question_policy


def make_question(
    *,
    question_id: str = "q-1",
    text: str = "Do you encrypt customer data at rest?",
    required_control: str = "encryption_at_rest",
) -> Question:
    return Question(
        id=question_id,
        question_text=text,
        required_control=required_control,
        risk_domain="security",
    )


def make_fact(
    *,
    fact_id: str = "fact-1",
    category: str = "encryption_at_rest",
    claim: str = "Customer data is encrypted at rest.",
    evidence_quote: str = "All customer data is encrypted at rest using AES-256.",
    confidence: float = 0.95,
) -> Fact:
    return Fact(
        id=fact_id,
        category=category,
        claim=claim,
        evidence_quote=evidence_quote,
        source_document="security.md",
        source_chunk_id="chunk-1",
        confidence=confidence,
    )


def test_no_evidence_means_deficit():
    decision = evaluate_question_policy(make_question(), [])

    assert decision.status is PolicyStatus.DEFICIT


def test_soc2_not_claimed_without_soc2_fact():
    question = make_question(
        text="Are you SOC 2 Type II compliant?",
        required_control="soc2_type_ii",
    )
    unrelated_fact = make_fact(
        category="audit_logging",
        claim="Application events are written to audit logs.",
        evidence_quote="Administrative changes are recorded in audit logs.",
    )

    decision = evaluate_question_policy(question, [unrelated_fact])

    assert decision.status is PolicyStatus.DEFICIT
    assert decision.cited_fact_ids == []


def test_supported_question_gets_supported_status():
    decision = evaluate_question_policy(make_question(), [make_fact()])

    assert decision.status is PolicyStatus.SUPPORTED


def test_partial_evidence_gets_partial_status():
    weak_fact = make_fact(confidence=0.55)

    decision = evaluate_question_policy(make_question(), [weak_fact])

    assert decision.status is PolicyStatus.PARTIAL
    assert decision.cited_fact_ids == [weak_fact.id]


def test_deficit_has_no_citations():
    decision = evaluate_question_policy(make_question(), [])

    assert decision.cited_fact_ids == []


def test_supported_answer_requires_citation():
    fact = make_fact()

    decision = evaluate_question_policy(make_question(), [fact])

    assert decision.status is PolicyStatus.SUPPORTED
    assert decision.cited_fact_ids == [fact.id]


@pytest.mark.parametrize(
    ("facts", "expected_phrase"),
    [
        ([], "No explicit evidence"),
        ([make_fact(confidence=0.5)], "partial or weak evidence"),
        ([make_fact()], "Strong, explicit evidence"),
    ],
)
def test_policy_reason_is_human_readable(facts, expected_phrase):
    decision = evaluate_question_policy(make_question(), facts)

    assert expected_phrase in decision.reason
    assert decision.reason.endswith(".")
    assert len(decision.reason.split()) >= 8
