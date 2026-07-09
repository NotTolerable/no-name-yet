"""Rule-based Technical State Map extraction helpers."""

from collections.abc import Iterable
from hashlib import sha256
from pathlib import Path
import re

from core.models import Document, DocumentChunk, Fact


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
                    )
                )

    return facts
