"""Rule-based Technical State Map extraction helpers."""

from collections.abc import Iterable
from hashlib import sha256
from pathlib import Path
import re

from core.models import (
    Document,
    DocumentChunk,
    Fact,
    FactApplicability,
    FactPolarity,
    FactReviewStatus,
)


SUPPORTED_DOCUMENT_SUFFIXES = {".md", ".txt"}

# These patterns identify explicit mentions only. They intentionally do not try
# to decide whether a control is sufficient or whether a company is compliant.
FACT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "tenant_isolation",
        re.compile(
            r"\b(?:tenant[\s_-]+isolation|tenant[\s_-]*id|"
            r"scop(?:e|ed|ing)\b[^.]*\btenant)\b",
            re.IGNORECASE,
        ),
    ),
    ("encryption", re.compile(r"\bencrypt(?:ed|ion|ing)?\b", re.IGNORECASE)),
    (
        "model_training",
        re.compile(
            r"\b(?:model training|train(?:ed|ing)?\b[^.]*\bmodel|"
            r"models?\b[^.]*\btrain(?:ed|ing)?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "prompt_retention",
        re.compile(
            r"\b(?:prompt(?:s)?\b[^.]*\b(?:retain|retained|retention|store|"
            r"stored|storage)|(?:retain|retained|retention|store|stored|storage)"
            r"\b[^.]*\bprompts?)\b",
            re.IGNORECASE,
        ),
    ),
    ("audit_logging", re.compile(r"\baudit[\s_-]+logs?(?:ging)?\b", re.IGNORECASE)),
    (
        "admin_access",
        re.compile(
            r"\b(?:admin(?:istrator|istrative)?|privileged)[\s_-]+access\b",
            re.IGNORECASE,
        ),
    ),
    (
        "incident_response",
        re.compile(r"\bincident[\s_-]+response\b", re.IGNORECASE),
    ),
    ("soc2", re.compile(r"\bsoc\s*2(?:\s+type\s+(?:i{1,2}|[12]))?\b", re.IGNORECASE)),
    ("hipaa", re.compile(r"\bhipaa\b", re.IGNORECASE)),
    (
        "prompt_injection_testing",
        re.compile(r"\bprompt[\s_-]+injection\b", re.IGNORECASE),
    ),
)

# Polarity is relative to each category's canonical proposition. These narrow,
# category-specific rules intentionally avoid treating every grammatical "not"
# as evidence that the proposition is false.
NEGATIVE_POLARITY_PATTERNS: dict[str, re.Pattern[str]] = {
    "tenant_isolation": re.compile(
        r"\b(?:tenant[\s_-]+isolation\s+(?:is\s+)?not|"
        r"not\s+(?:isolated|scoped)\b[^.]*\btenant)", re.IGNORECASE
    ),
    "encryption": re.compile(
        r"\b(?:is|are|was|were)\s+not\s+encrypted\b|\bno\s+encryption\b",
        re.IGNORECASE,
    ),
    "model_training": re.compile(
        r"\b(?:not|never)\s+(?:used\s+)?(?:for\s+)?model\s+training\b|"
        r"\bdo(?:es)?\s+not\s+[^.]*\btrain\b[^.]*\bmodels?\b",
        re.IGNORECASE,
    ),
    "prompt_retention": re.compile(
        r"\bprompts?\s+(?:are\s+)?not\s+(?:retained|stored)\b|"
        r"\bdo(?:es)?\s+not\s+(?:retain|store)\s+prompts?\b",
        re.IGNORECASE,
    ),
    "audit_logging": re.compile(
        r"\bno\s+audit\s+logs?\b|\baudit\s+logging\s+(?:is\s+)?not\b",
        re.IGNORECASE,
    ),
    "admin_access": re.compile(
        r"\bno\s+(?:admin(?:istrative)?|privileged)\s+access\b",
        re.IGNORECASE,
    ),
    "incident_response": re.compile(
        r"\bno\s+incident[\s_-]+response\s+(?:plan|policy|process)\b|"
        r"\bincident[\s_-]+response\s+(?:is\s+)?not\s+(?:defined|documented)",
        re.IGNORECASE,
    ),
    "soc2": re.compile(
        r"\b(?:not|never)\s+(?:completed|certified|compliant)\b[^.]*\bsoc\s*2\b|"
        r"\bsoc\s*2\b[^.]*\b(?:not\s+(?:completed|certified|compliant)|no\s+report)\b",
        re.IGNORECASE,
    ),
    "hipaa": re.compile(
        r"\bnot\s+hipaa\s+(?:compliant|certified)\b|"
        r"\bhipaa\s+compliance\s+(?:is\s+)?not\s+(?:established|documented)",
        re.IGNORECASE,
    ),
    "prompt_injection_testing": re.compile(
        r"\bdo(?:es)?\s+not\s+(?:perform|conduct|run)\s+prompt[\s_-]+injection\b|"
        r"\bno\s+prompt[\s_-]+injection\s+testing\b",
        re.IGNORECASE,
    ),
}

POSITIVE_POLARITY_PATTERNS: dict[str, re.Pattern[str]] = {
    "tenant_isolation": re.compile(
        r"\b(?:tenant[\s_-]+isolation|tenant[\s_-]*id|"
        r"scop(?:e|ed|ing)\b[^.]*\btenant)\b", re.IGNORECASE
    ),
    "encryption": re.compile(r"\bencrypt(?:ed|ion|ing)?\b", re.IGNORECASE),
    "model_training": re.compile(
        r"\b(?:used\s+for\s+model\s+training|train(?:ed|ing)?\b[^.]*\bmodel)",
        re.IGNORECASE,
    ),
    "prompt_retention": re.compile(
        r"\bprompts?\s+(?:are\s+)?(?:retained|stored)\b|"
        r"\b(?:retain|store)\s+prompts?\b",
        re.IGNORECASE,
    ),
    "audit_logging": re.compile(
        r"\b(?:record(?:ed|s)?|writ(?:e|ten)|produce[sd]?)\b[^.]*\baudit\s+logs?\b|"
        r"\baudit\s+logging\s+(?:is\s+)?(?:enabled|implemented)",
        re.IGNORECASE,
    ),
    "admin_access": re.compile(
        r"\b(?:admin(?:istrative)?|privileged)\s+access\b[^.]*\b"
        r"(?:approval|restrict(?:ed|ion)?|require[sd]?)\b",
        re.IGNORECASE,
    ),
    "incident_response": re.compile(
        r"\bincident[\s_-]+response\s+(?:plan|policy|process)\b",
        re.IGNORECASE,
    ),
    "soc2": re.compile(
        r"\b(?:completed|certified|compliant)\b[^.]*\bsoc\s*2\b|"
        r"\bsoc\s*2\b[^.]*\b(?:report\s+is\s+available|certified|compliant)",
        re.IGNORECASE,
    ),
    "hipaa": re.compile(
        r"\bhipaa\s+(?:compliant|compliance\s+(?:is\s+)?documented)\b",
        re.IGNORECASE,
    ),
    "prompt_injection_testing": re.compile(
        r"\b(?:perform(?:s|ed)?|conduct(?:s|ed)?|run[ns]?)\b[^.]*"
        r"\bprompt[\s_-]+injection\s+test(?:ing|s)?\b|"
        r"\bprompt[\s_-]+injection\s+testing\s+(?:is\s+)?performed\b",
        re.IGNORECASE,
    ),
}

# Non-applicability must explicitly use the category's canonical proposition as
# its subject. A generic "not applicable" elsewhere in the sentence is not
# enough to mark the extracted control fact as not applicable.
NOT_APPLICABLE_PATTERNS: dict[str, re.Pattern[str]] = {
    "tenant_isolation": re.compile(
        r"\btenant(?:[\s_-]+data)?[\s_-]+(?:isolation|scoping)\s+"
        r"(?:(?:is\s+)?not\s+applicable|does\s+not\s+apply)\b",
        re.IGNORECASE,
    ),
    "encryption": re.compile(
        r"\bencryption(?:\s+at\s+rest)?\s+"
        r"(?:(?:is\s+)?not\s+applicable|does\s+not\s+apply)\b",
        re.IGNORECASE,
    ),
    "model_training": re.compile(
        r"\bmodel\s+training\s+"
        r"(?:(?:is\s+)?not\s+applicable|does\s+not\s+apply)\b",
        re.IGNORECASE,
    ),
    "prompt_retention": re.compile(
        r"\bprompt\s+retention\s+"
        r"(?:(?:is\s+)?not\s+applicable|does\s+not\s+apply)\b",
        re.IGNORECASE,
    ),
    "audit_logging": re.compile(
        r"\baudit\s+logging\s+"
        r"(?:(?:is\s+)?not\s+applicable|does\s+not\s+apply)\b",
        re.IGNORECASE,
    ),
    "admin_access": re.compile(
        r"\b(?:administrative|privileged)\s+access\s+"
        r"(?:(?:is\s+)?not\s+applicable|does\s+not\s+apply)\b",
        re.IGNORECASE,
    ),
    "incident_response": re.compile(
        r"\bincident\s+response\s+"
        r"(?:(?:is\s+)?not\s+applicable|does\s+not\s+apply)\b",
        re.IGNORECASE,
    ),
    "soc2": re.compile(
        r"\bsoc\s*2(?:\s+type\s+(?:i{1,2}|[12]))?\s+"
        r"(?:(?:is\s+)?not\s+applicable|does\s+not\s+apply)\b",
        re.IGNORECASE,
    ),
    "hipaa": re.compile(
        r"\bhipaa(?:\s+compliance)?\s+"
        r"(?:(?:is\s+)?not\s+applicable|does\s+not\s+apply)\b",
        re.IGNORECASE,
    ),
    "prompt_injection_testing": re.compile(
        r"\bprompt[\s_-]+injection\s+testing\s+"
        r"(?:(?:is\s+)?not\s+applicable|does\s+not\s+apply)\b",
        re.IGNORECASE,
    ),
}


def _fact_polarity(category: str, text: str) -> FactPolarity:
    applicability_pattern = NOT_APPLICABLE_PATTERNS.get(category)
    if applicability_pattern is not None and applicability_pattern.search(text):
        return FactPolarity.NEUTRAL
    negative_pattern = NEGATIVE_POLARITY_PATTERNS.get(category)
    if negative_pattern is not None and negative_pattern.search(text):
        return FactPolarity.NEGATIVE
    positive_pattern = POSITIVE_POLARITY_PATTERNS.get(category)
    if positive_pattern is not None and positive_pattern.search(text):
        return FactPolarity.POSITIVE
    return FactPolarity.NEUTRAL


def _fact_applicability(
    category: str, text: str, polarity: FactPolarity
) -> FactApplicability:
    pattern = NOT_APPLICABLE_PATTERNS.get(category)
    if pattern is not None and pattern.search(text):
        return FactApplicability.NOT_APPLICABLE
    if polarity is FactPolarity.NEUTRAL:
        return FactApplicability.UNSPECIFIED
    return FactApplicability.APPLICABLE


def _stable_id(prefix: str, *parts: object) -> str:
    material = "\x1f".join(str(part) for part in parts)
    digest = sha256(material.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def load_documents_from_directory(path: str | Path) -> list[Document]:
    """Load supported text documents from ``path`` in deterministic order."""

    directory = Path(path)
    if not directory.is_dir():
        raise ValueError(f"Document directory does not exist: {directory}")

    documents: list[Document] = []
    for file_path in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_DOCUMENT_SUFFIXES:
            continue
        text = file_path.read_text(encoding="utf-8")
        documents.append(
            Document(
                id=_stable_id("doc", file_path.name, text),
                file_name=file_path.name,
                text=text,
            )
        )
    return documents


def chunk_document(document: Document) -> list[DocumentChunk]:
    """Split a document on blank lines while preserving source traceability."""

    sections = [
        section.strip()
        for section in re.split(r"\n\s*\n", document.text)
        if section.strip()
    ]
    return [
        DocumentChunk(
            id=_stable_id("chunk", document.id, index, text),
            document_id=document.id,
            chunk_index=index,
            text=text,
            source_label=f"{document.file_name}#chunk-{index}",
        )
        for index, text in enumerate(sections)
    ]


def _sentences(text: str) -> Iterable[str]:
    """Yield exact non-empty sentence-like spans from a chunk."""

    for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
        cleaned = sentence.strip()
        if cleaned:
            yield cleaned


def _source_document(chunk: DocumentChunk) -> str:
    return chunk.source_label.rsplit("#chunk-", maxsplit=1)[0]


def extract_facts_from_chunks(chunks: list[DocumentChunk]) -> list[Fact]:
    """Extract explicitly documented facts using conservative keyword rules."""

    facts: list[Fact] = []
    seen: set[tuple[str, str, str]] = set()

    for chunk in chunks:
        for evidence_quote in _sentences(chunk.text):
            for category, pattern in FACT_PATTERNS:
                if not pattern.search(evidence_quote):
                    continue

                identity = (chunk.id, category, evidence_quote)
                if identity in seen:
                    continue
                seen.add(identity)

                polarity = _fact_polarity(category, evidence_quote)
                facts.append(
                    Fact(
                        id=_stable_id("fact", *identity),
                        category=category,
                        # Preserve the documented statement rather than adding an
                        # inferred positive or compliance claim.
                        claim=evidence_quote,
                        evidence_quote=evidence_quote,
                        source_document=_source_document(chunk),
                        source_chunk_id=chunk.id,
                        confidence=0.9,
                        polarity=polarity,
                        # This extractor is curated and deterministic. Future
                        # untrusted/model extractors must emit CANDIDATE instead.
                        review_status=FactReviewStatus.APPROVED,
                        applicability=_fact_applicability(
                            category, evidence_quote, polarity
                        ),
                    )
                )

    return facts
