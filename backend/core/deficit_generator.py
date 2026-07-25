"""Deterministic remediation generation for compliance deficits."""

from core.models import PolicyDecision, PolicyStatus, Question, RemediationTask


HIGH_SEVERITY_CONTROLS = {
    "soc2",
    "soc2_type_ii",
    "hipaa",
    "hipaa_compliance",
    "encryption",
    "encryption_at_rest",
    "tenant_isolation",
    "pii_scrubbing",
    "audit_logging",
    "prompt_retention",
    "model_training_opt_out",
    "incident_response",
    "incident_response_policy",
}


def _control_name(required_control: str) -> str:
    return " ".join(required_control.replace("-", "_").split("_")).strip()


def generate_remediation_task(
    question: Question, policy_decision: PolicyDecision
) -> RemediationTask | None:
    """Create a remediation task for a deficit without asserting compliance."""

    if policy_decision.question_id != question.id:
        raise ValueError("Policy decision does not belong to this question")
    if policy_decision.evidence_status is not PolicyStatus.DEFICIT:
        return None

    control_name = _control_name(question.required_control)
    severity = (
        "high" if question.required_control.lower() in HIGH_SEVERITY_CONTROLS else "medium"
    )
    owner = "security" if question.risk_domain.lower() == "security" else "compliance"

    return RemediationTask(
        question_id=question.id,
        title=f"Provide evidence for {control_name}",
        description=(
            f"No explicit evidence currently supports the {control_name} "
            "requirement. Verify whether the control exists, document its actual "
            "state, and obtain reviewable source evidence before making a "
            "buyer-facing claim."
        ),
        severity=severity,
        suggested_owner=owner,
    )
