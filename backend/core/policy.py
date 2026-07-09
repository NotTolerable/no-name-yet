"""Deterministic policy gate for evidence-backed questionnaire decisions."""

from collections.abc import Iterable

from core.models import Fact, PolicyDecision, PolicyStatus, Question


STRONG_EVIDENCE_THRESHOLD = 0.8

# Risky claims require evidence that explicitly names the requested control. The
# aliases are intentionally narrow: false deficits are safer than false claims.
RISKY_CONTROL_TERMS: dict[str, tuple[str, ...]] = {
    "soc2_type_ii": ("soc 2 type ii", "soc2 type ii", "soc 2 type 2"),
    "hipaa_compliance": ("hipaa compliant", "hipaa compliance"),
    "encryption_at_rest": ("encryption at rest", "encrypted at rest"),
    "tenant_isolation": ("tenant isolation", "tenant isolated", "tenant_id"),
    "pii_scrubbing": ("pii scrubbing", "pii scrubbed", "scrub pii"),
    "audit_logging": ("audit logging", "audit logs", "audit log"),
    "prompt_retention": ("prompt retention", "retain prompts", "prompt storage"),
    "model_training_opt_out": (
        "model training opt-out",
        "model training opt out",
        "not used for model training",
        "not train on",
    ),
    "incident_response_policy": (
        "incident response policy",
        "incident response plan",
    ),
}


def _normalize(value: str) -> str:
    """Normalize labels while retaining enough text for phrase matching."""

    return " ".join(value.lower().replace("-", " ").replace("_", " ").split())


def _risky_control_for(question: Question) -> str | None:
    question_text = _normalize(question.question_text)
    required_control = _normalize(question.required_control)

    for control, aliases in RISKY_CONTROL_TERMS.items():
        normalized_control = _normalize(control)
        if required_control == normalized_control:
            return control
        if any(_normalize(alias) in question_text for alias in aliases):
            return control
    return None


def _fact_explicitly_supports(control: str, fact: Fact) -> bool:
    searchable_text = _normalize(
        " ".join((fact.category, fact.claim, fact.evidence_quote))
    )
    return any(
        _normalize(alias) in searchable_text
        for alias in RISKY_CONTROL_TERMS[control]
    )


def _eligible_facts(question: Question, matching_facts: Iterable[Fact]) -> list[Fact]:
    facts = list(matching_facts)
    risky_control = _risky_control_for(question)
    if risky_control is None:
        return facts
    return [fact for fact in facts if _fact_explicitly_supports(risky_control, fact)]


def evaluate_question_policy(
    question: Question, matching_facts: list[Fact]
) -> PolicyDecision:
    """Evaluate whether available facts permit a positive buyer-facing claim.

    This function is deliberately deterministic. It does not draft an answer and
    does not infer that an unrelated fact supports a high-risk control.
    """

    eligible_facts = _eligible_facts(question, matching_facts)

    if not eligible_facts:
        return PolicyDecision(
            question_id=question.id,
            status=PolicyStatus.DEFICIT,
            reason=(
                "No explicit evidence was found for this requirement; "
                "a positive claim is not permitted."
            ),
            cited_fact_ids=[],
        )

    cited_fact_ids = [fact.id for fact in eligible_facts]
    if any(fact.confidence >= STRONG_EVIDENCE_THRESHOLD for fact in eligible_facts):
        return PolicyDecision(
            question_id=question.id,
            status=PolicyStatus.SUPPORTED,
            reason=(
                "Strong, explicit evidence supports this requirement and the "
                "supporting facts are cited."
            ),
            cited_fact_ids=cited_fact_ids,
        )

    return PolicyDecision(
        question_id=question.id,
        status=PolicyStatus.PARTIAL,
        reason=(
            "Only partial or weak evidence was found; any response must state "
            "this limitation and remain qualified."
        ),
        cited_fact_ids=cited_fact_ids,
    )
