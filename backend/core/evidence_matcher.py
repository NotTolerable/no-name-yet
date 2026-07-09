"""Deterministic evidence matching for questionnaire requirements."""

import re

from core.models import EvidenceMatch, Fact, Question


CATEGORY_ALIASES = {
    "encryption_at_rest": "encryption",
    "hipaa_compliance": "hipaa",
    "incident_response_policy": "incident_response",
    "soc2_type_ii": "soc2",
}

# These claims must never be matched through generic keywords or domain context.
# They require a fact in the corresponding explicit category.
EXPLICIT_EVIDENCE_CONTROLS = {
    "soc2": "soc2",
    "hipaa": "hipaa",
}

DOMAIN_CATEGORIES = {
    "security": {
        "admin_access",
        "audit_logging",
        "encryption",
        "incident_response",
        "prompt_injection_testing",
        "tenant_isolation",
    },
    "privacy": {"hipaa", "model_training", "pii_scrubbing", "prompt_retention"},
    "ai_governance": {
        "model_training",
        "prompt_injection_testing",
        "prompt_retention",
    },
    "compliance": {"hipaa", "incident_response", "soc2"},
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "be",
    "customer",
    "data",
    "do",
    "does",
    "for",
    "how",
    "is",
    "of",
    "or",
    "the",
    "to",
    "what",
    "with",
    "you",
    "your",
}


def _normalize_label(value: str) -> str:
    return "_".join(re.findall(r"[a-z0-9]+", value.lower()))


def _canonical_category(value: str) -> str:
    normalized = _normalize_label(value)
    return CATEGORY_ALIASES.get(normalized, normalized)


def _keywords(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower().replace("soc 2", "soc2"))
        if len(token) > 2 and token not in STOP_WORDS
    }


def _make_match(
    question: Question, fact: Fact, relevance: float, reason: str
) -> EvidenceMatch:
    return EvidenceMatch(
        question_id=question.id,
        fact_id=fact.id,
        relevance=relevance,
        reason=reason,
    )


def match_question_to_facts(
    question: Question, facts: list[Fact]
) -> list[EvidenceMatch]:
    """Return ranked evidence candidates using three conservative match tiers.

    Higher-quality tiers short-circuit lower ones, preventing broad risk-domain
    context from diluting an available direct control match.
    """

    required_category = _canonical_category(question.required_control)

    direct_matches = [
        _make_match(
            question,
            fact,
            1.0,
            (
                "The fact category directly matches the question's required "
                f"control ({question.required_control})."
            ),
        )
        for fact in facts
        if _canonical_category(fact.category) == required_category
    ]
    if direct_matches:
        return direct_matches

    if required_category in EXPLICIT_EVIDENCE_CONTROLS:
        return []

    question_keywords = _keywords(
        f"{question.required_control} {question.question_text}"
    )
    keyword_matches: list[EvidenceMatch] = []
    for fact in facts:
        fact_keywords = _keywords(
            f"{fact.category} {fact.claim} {fact.evidence_quote}"
        )
        overlap = question_keywords & fact_keywords
        if not overlap:
            continue
        coverage = len(overlap) / max(1, len(question_keywords))
        if coverage < 0.2:
            continue
        relevance = min(0.85, 0.5 + coverage * 0.35)
        keyword_matches.append(
            _make_match(
                question,
                fact,
                relevance,
                "The question and fact share relevant keywords: "
                + ", ".join(sorted(overlap))
                + ".",
            )
        )
    if keyword_matches:
        return sorted(keyword_matches, key=lambda match: (-match.relevance, match.fact_id))

    risk_domain = _normalize_label(question.risk_domain)
    eligible_categories = DOMAIN_CATEGORIES.get(risk_domain, set())
    domain_matches = [
        _make_match(
            question,
            fact,
            0.3,
            (
                f"The fact is related to the question's {question.risk_domain} "
                "risk domain, but does not directly match the required control."
            ),
        )
        for fact in facts
        if _canonical_category(fact.category) in eligible_categories
    ]
    return sorted(domain_matches, key=lambda match: match.fact_id)
