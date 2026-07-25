import pytest

from core.answer_generator import generate_answer
from core.models import (
    AnswerValue,
    Fact,
    FactApplicability,
    FactPolarity,
    FactReviewStatus,
    PolicyDecision,
    PolicyStatus,
    Question,
    QuestionResponseKind,
)


def make_question():
    return Question(
        id="q-1",
        question_text="Is customer data encrypted at rest?",
        required_control="encryption_at_rest",
        risk_domain="security",
        response_kind=QuestionResponseKind.BINARY,
        affirmative_polarity=FactPolarity.POSITIVE,
    )


def make_fact(
    *,
    fact_id="fact-encryption",
    claim="Customer data is encrypted at rest.",
    evidence_quote="Customer data is encrypted at rest using managed keys.",
):
    return Fact(
        id=fact_id,
        category="encryption",
        claim=claim,
        evidence_quote=evidence_quote,
        source_document="security.md",
        source_chunk_id="chunk-1",
        confidence=0.95,
        polarity=FactPolarity.POSITIVE,
        review_status=FactReviewStatus.APPROVED,
        applicability=FactApplicability.APPLICABLE,
    )


def make_decision(status, cited_fact_ids=None):
    return PolicyDecision(
        question_id="q-1",
        status=status,
        answer_value=(
            AnswerValue.UNKNOWN
            if status is PolicyStatus.DEFICIT
            else AnswerValue.YES
        ),
        response_kind=QuestionResponseKind.BINARY,
        reason="Deterministic policy evaluation completed.",
        cited_fact_ids=cited_fact_ids or [],
    )


def test_supported_answer_includes_citation():
    fact = make_fact()

    answer = generate_answer(
        make_question(),
        make_decision(PolicyStatus.SUPPORTED, [fact.id]),
        [fact],
    )

    assert answer.citations == [fact.evidence_quote]
    assert answer.status is PolicyStatus.SUPPORTED


def test_supported_answer_does_not_add_unrelated_claims():
    approved_fact = make_fact()
    unrelated_fact = make_fact(
        fact_id="fact-soc2",
        claim="The company has completed SOC 2 Type II.",
        evidence_quote="A SOC 2 Type II report is available.",
    )

    answer = generate_answer(
        make_question(),
        make_decision(PolicyStatus.SUPPORTED, [approved_fact.id]),
        [approved_fact, unrelated_fact],
    )

    assert answer.answer_text == approved_fact.claim
    assert "SOC 2" not in answer.answer_text
    assert unrelated_fact.evidence_quote not in answer.citations


def test_deficit_does_not_generate_positive_claim():
    answer = generate_answer(
        make_question(),
        make_decision(PolicyStatus.DEFICIT),
        [],
    )

    assert answer.status is PolicyStatus.DEFICIT
    assert "No evidence-backed answer was generated" in answer.answer_text
    assert answer.citations == []
    assert "encrypted" not in answer.answer_text.lower()


def test_partial_answer_is_qualified():
    fact = make_fact()

    answer = generate_answer(
        make_question(),
        make_decision(PolicyStatus.PARTIAL, [fact.id]),
        [fact],
    )

    assert answer.status is PolicyStatus.PARTIAL
    assert "limited available evidence" in answer.answer_text
    assert "does not fully establish" in answer.answer_text
    assert answer.citations == [fact.evidence_quote]


def test_supported_answer_fails_closed_without_cited_fact():
    with pytest.raises(ValueError, match="requires at least one policy-cited fact"):
        generate_answer(
            make_question(),
            make_decision(PolicyStatus.SUPPORTED, ["missing-fact"]),
            [],
        )


def test_non_approved_fact_cannot_reach_buyer_facing_answer():
    fact = make_fact().model_copy(
        update={"review_status": FactReviewStatus.CANDIDATE}
    )

    with pytest.raises(ValueError, match="requires at least one policy-cited fact"):
        generate_answer(
            make_question(),
            make_decision(PolicyStatus.SUPPORTED, [fact.id]),
            [fact],
        )
