"""Deterministic answer generation from policy-approved evidence."""

from core.models import Answer, Fact, PolicyDecision, PolicyStatus, Question


DEFICIT_ANSWER = (
    "No evidence-backed answer was generated because the required supporting "
    "evidence is missing."
)


def _approved_facts(
    policy_decision: PolicyDecision, cited_facts: list[Fact]
) -> list[Fact]:
    facts_by_id = {fact.id: fact for fact in cited_facts}
    return [
        facts_by_id[fact_id]
        for fact_id in policy_decision.cited_fact_ids
        if fact_id in facts_by_id
    ]


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def generate_answer(
    question: Question,
    policy_decision: PolicyDecision,
    cited_facts: list[Fact],
) -> Answer:
    """Generate an answer using only facts cited by the policy decision."""

    if policy_decision.question_id != question.id:
        raise ValueError("Policy decision does not belong to this question")

    if policy_decision.status is PolicyStatus.DEFICIT:
        return Answer(
            question_id=question.id,
            status=PolicyStatus.DEFICIT,
            answer_text=DEFICIT_ANSWER,
            citations=[],
            policy_reason=policy_decision.reason,
        )

    approved_facts = _approved_facts(policy_decision, cited_facts)
    if not approved_facts:
        raise ValueError(
            "A supported or partial answer requires at least one policy-cited fact"
        )

    documented_claims = _unique([fact.claim.strip() for fact in approved_facts])
    citations = _unique([fact.evidence_quote.strip() for fact in approved_facts])

    if policy_decision.status is PolicyStatus.PARTIAL:
        answer_text = (
            "Based on the limited available evidence, "
            + " ".join(documented_claims)
            + " This evidence does not fully establish the requested control."
        )
    else:
        answer_text = " ".join(documented_claims)

    return Answer(
        question_id=question.id,
        status=policy_decision.status,
        answer_text=answer_text,
        citations=citations,
        policy_reason=policy_decision.reason,
    )
