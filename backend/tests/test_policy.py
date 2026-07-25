import pytest

from core.models import (
    AnswerValue,
    Fact,
    FactApplicability,
    FactPolarity,
    FactReviewStatus,
    PolicyStatus,
    Question,
    QuestionResponseKind,
)
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
        response_kind=QuestionResponseKind.BINARY,
        affirmative_polarity=FactPolarity.POSITIVE,
    )


def make_fact(
    *,
    fact_id: str = "fact-1",
    category: str = "encryption_at_rest",
    claim: str = "Customer data is encrypted at rest.",
    evidence_quote: str = "All customer data is encrypted at rest using AES-256.",
    confidence: float = 0.95,
    polarity: FactPolarity = FactPolarity.POSITIVE,
    review_status: FactReviewStatus = FactReviewStatus.APPROVED,
    applicability: FactApplicability = FactApplicability.APPLICABLE,
) -> Fact:
    return Fact(
        id=fact_id,
        category=category,
        claim=claim,
        evidence_quote=evidence_quote,
        source_document="security.md",
        source_chunk_id="chunk-1",
        confidence=confidence,
        polarity=polarity,
        review_status=review_status,
        applicability=applicability,
    )


def test_no_evidence_means_deficit():
    decision = evaluate_question_policy(make_question(), [])

    assert decision.status is PolicyStatus.DEFICIT
    assert decision.answer_value is AnswerValue.UNKNOWN


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
    assert decision.answer_value is AnswerValue.YES


def test_partial_evidence_gets_partial_status():
    weak_fact = make_fact(confidence=0.55)

    decision = evaluate_question_policy(make_question(), [weak_fact])

    assert decision.status is PolicyStatus.PARTIAL
    assert decision.answer_value is AnswerValue.YES
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


def test_strong_negative_evidence_is_supported_with_no_answer():
    question = make_question(
        text="Are you SOC 2 Type II certified?",
        required_control="soc2_type_ii",
    )
    fact = make_fact(
        category="soc2",
        claim="We have not completed a SOC 2 Type II audit.",
        evidence_quote="We have not completed a SOC 2 Type II audit.",
        polarity=FactPolarity.NEGATIVE,
    )

    decision = evaluate_question_policy(question, [fact])

    assert decision.evidence_status is PolicyStatus.SUPPORTED
    assert decision.answer_value is AnswerValue.NO
    assert decision.cited_fact_ids == [fact.id]


def test_negative_question_orientation_reverses_answer_mapping():
    question = Question(
        id="q-negative-orientation",
        question_text="Do you avoid using customer prompts for model training?",
        required_control="model_training",
        risk_domain="security",
        response_kind=QuestionResponseKind.BINARY,
        affirmative_polarity=FactPolarity.NEGATIVE,
    )
    fact = make_fact(
        category="model_training",
        claim="Customer prompts are not used for model training.",
        evidence_quote="Customer prompts are not used for model training.",
        polarity=FactPolarity.NEGATIVE,
    )

    decision = evaluate_question_policy(question, [fact])

    assert decision.evidence_status is PolicyStatus.SUPPORTED
    assert decision.answer_value is AnswerValue.YES


@pytest.mark.parametrize(
    "review_status",
    [
        FactReviewStatus.CANDIDATE,
        FactReviewStatus.REJECTED,
        FactReviewStatus.SUPERSEDED,
    ],
)
def test_non_approved_fact_cannot_support_policy(review_status):
    decision = evaluate_question_policy(
        make_question(), [make_fact(review_status=review_status)]
    )

    assert decision.evidence_status is PolicyStatus.DEFICIT
    assert decision.answer_value is AnswerValue.UNKNOWN
    assert decision.cited_fact_ids == []


def test_conflicting_approved_evidence_is_partial_and_unknown():
    positive = make_fact(fact_id="fact-positive")
    negative = make_fact(
        fact_id="fact-negative",
        claim="Customer data is not encrypted at rest.",
        evidence_quote="Customer data is not encrypted at rest.",
        polarity=FactPolarity.NEGATIVE,
    )

    decision = evaluate_question_policy(make_question(), [positive, negative])

    assert decision.evidence_status is PolicyStatus.PARTIAL
    assert decision.answer_value is AnswerValue.UNKNOWN
    assert decision.cited_fact_ids == [positive.id, negative.id]


def test_not_applicable_requires_explicit_evidence():
    fact = make_fact(
        claim="Encryption at rest does not apply to this stateless component.",
        evidence_quote="Encryption at rest does not apply to this stateless component.",
        polarity=FactPolarity.NEUTRAL,
        applicability=FactApplicability.NOT_APPLICABLE,
    )

    decision = evaluate_question_policy(make_question(), [fact])

    assert decision.evidence_status is PolicyStatus.SUPPORTED
    assert decision.answer_value is AnswerValue.NOT_APPLICABLE
    assert decision.cited_fact_ids == [fact.id]


def test_unrelated_not_applicable_clause_does_not_change_answer_value():
    fact = make_fact(
        claim=(
            "Encryption at rest is enabled; automatic key rotation is not "
            "applicable."
        ),
        evidence_quote=(
            "Encryption at rest is enabled; automatic key rotation is not "
            "applicable."
        ),
        polarity=FactPolarity.POSITIVE,
        applicability=FactApplicability.APPLICABLE,
    )

    decision = evaluate_question_policy(make_question(), [fact])

    assert decision.evidence_status is PolicyStatus.SUPPORTED
    assert decision.answer_value is AnswerValue.YES


def test_not_applicable_fact_for_another_control_cannot_authorize_answer():
    fact = make_fact(
        category="prompt_retention",
        claim="Prompt retention is not applicable; encryption at rest is documented.",
        evidence_quote=(
            "Prompt retention is not applicable; encryption at rest is documented."
        ),
        polarity=FactPolarity.NEUTRAL,
        applicability=FactApplicability.NOT_APPLICABLE,
    )

    decision = evaluate_question_policy(make_question(), [fact])

    assert decision.evidence_status is PolicyStatus.PARTIAL
    assert decision.answer_value is AnswerValue.UNKNOWN


@pytest.mark.parametrize(
    "review_status",
    [
        FactReviewStatus.CANDIDATE,
        FactReviewStatus.REJECTED,
        FactReviewStatus.SUPERSEDED,
    ],
)
def test_non_approved_not_applicable_fact_is_ignored(review_status):
    fact = make_fact(
        polarity=FactPolarity.NEUTRAL,
        applicability=FactApplicability.NOT_APPLICABLE,
        review_status=review_status,
    )

    decision = evaluate_question_policy(make_question(), [fact])

    assert decision.evidence_status is PolicyStatus.DEFICIT
    assert decision.answer_value is AnswerValue.UNKNOWN
