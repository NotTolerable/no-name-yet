from core.evidence_matcher import match_question_to_facts
from core.models import (
    Fact,
    FactApplicability,
    FactPolarity,
    FactReviewStatus,
    Question,
    QuestionResponseKind,
)


def make_question(
    *,
    question_id="q-1",
    text="Do you isolate customer data by tenant?",
    required_control="tenant_isolation",
    risk_domain="security",
    response_kind=QuestionResponseKind.BINARY,
    affirmative_polarity=FactPolarity.POSITIVE,
):
    return Question(
        id=question_id,
        question_text=text,
        required_control=required_control,
        risk_domain=risk_domain,
        response_kind=response_kind,
        affirmative_polarity=affirmative_polarity,
    )


def make_fact(
    *,
    fact_id="fact-1",
    category="tenant_isolation",
    claim="Queries are scoped to the authenticated tenant.",
    evidence_quote="Every query is scoped using the authenticated tenant_id.",
    polarity=FactPolarity.POSITIVE,
    review_status=FactReviewStatus.APPROVED,
    applicability=FactApplicability.APPLICABLE,
):
    return Fact(
        id=fact_id,
        category=category,
        claim=claim,
        evidence_quote=evidence_quote,
        source_document="architecture.md",
        source_chunk_id="chunk-1",
        confidence=0.9,
        polarity=polarity,
        review_status=review_status,
        applicability=applicability,
    )


def test_matches_tenant_isolation_question():
    fact = make_fact()

    matches = match_question_to_facts(make_question(), [fact])

    assert [match.fact_id for match in matches] == [fact.id]
    assert matches[0].relevance == 1.0


def test_matches_model_training_question():
    question = make_question(
        text="Do you use customer inputs for model training?",
        required_control="model_training",
        risk_domain="ai_governance",
    )
    fact = make_fact(
        category="model_training",
        claim="Customer prompts are not used for model training.",
        evidence_quote="Customer prompts are not used for model training.",
    )

    matches = match_question_to_facts(question, [fact])

    assert [match.fact_id for match in matches] == [fact.id]


def test_returns_empty_for_soc2_without_evidence():
    question = make_question(
        text="Are you SOC 2 Type II compliant?",
        required_control="soc2_type_ii",
        risk_domain="compliance",
    )
    audit_fact = make_fact(category="audit_logging")

    assert match_question_to_facts(question, [audit_fact]) == []


def test_returns_empty_for_hipaa_without_evidence():
    question = make_question(
        text="Are you HIPAA compliant?",
        required_control="hipaa_compliance",
        risk_domain="compliance",
    )
    encryption_fact = make_fact(category="encryption")

    assert match_question_to_facts(question, [encryption_fact]) == []


def test_match_includes_reason():
    matches = match_question_to_facts(make_question(), [make_fact()])

    assert matches[0].reason
    assert "directly matches" in matches[0].reason


def test_match_references_existing_fact():
    facts = [make_fact(fact_id="fact-existing")]

    matches = match_question_to_facts(make_question(), facts)

    assert all(match.fact_id in {fact.id for fact in facts} for match in matches)


def test_uses_keyword_overlap_when_categories_differ():
    question = make_question(
        text="How are administrative actions logged?",
        required_control="security_event_records",
        response_kind=QuestionResponseKind.FREE_TEXT,
        affirmative_polarity=None,
    )
    fact = make_fact(
        category="audit_logging",
        claim="Administrative actions are recorded in audit logs.",
        evidence_quote="Administrative actions are recorded in audit logs.",
    )

    matches = match_question_to_facts(question, [fact])

    assert [match.fact_id for match in matches] == [fact.id]
    assert "keywords" in matches[0].reason


def test_uses_low_score_risk_domain_fallback():
    question = make_question(
        text="Describe the control review process.",
        required_control="control_review",
        risk_domain="security",
        response_kind=QuestionResponseKind.FREE_TEXT,
        affirmative_polarity=None,
    )
    fact = make_fact(category="incident_response")

    matches = match_question_to_facts(question, [fact])

    assert matches[0].relevance == 0.3
    assert "risk domain" in matches[0].reason


def test_only_approved_facts_are_matchable():
    for review_status in (
        FactReviewStatus.CANDIDATE,
        FactReviewStatus.REJECTED,
        FactReviewStatus.SUPERSEDED,
    ):
        fact = make_fact(review_status=review_status)
        assert match_question_to_facts(make_question(), [fact]) == []
