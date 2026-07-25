from core.fact_graph import (
    chunk_document,
    extract_facts_from_chunks,
    load_documents_from_directory,
)
from core.models import FactApplicability, FactPolarity, FactReviewStatus


def write_sample_documents(tmp_path):
    (tmp_path / "architecture.md").write_text(
        """# Architecture

All customer records include a tenant_id and application queries are scoped by authenticated tenant.

Administrative changes are recorded in audit logs.
""",
        encoding="utf-8",
    )
    (tmp_path / "ai-policy.txt").write_text(
        "Customer prompts are not used for model training.\n\nPrompts are retained for 30 days.",
        encoding="utf-8",
    )
    (tmp_path / "ignored.csv").write_text("not,a,source", encoding="utf-8")


def load_sample_chunks(tmp_path):
    write_sample_documents(tmp_path)
    documents = load_documents_from_directory(tmp_path)
    return [chunk for document in documents for chunk in chunk_document(document)]


def test_loads_sample_documents(tmp_path):
    write_sample_documents(tmp_path)

    documents = load_documents_from_directory(tmp_path)

    assert [document.file_name for document in documents] == [
        "ai-policy.txt",
        "architecture.md",
    ]
    assert all(document.text for document in documents)


def test_chunks_documents(tmp_path):
    write_sample_documents(tmp_path)
    documents = load_documents_from_directory(tmp_path)

    chunks = [chunk for document in documents for chunk in chunk_document(document)]

    assert len(chunks) == 5
    assert [chunk.chunk_index for chunk in chunk_document(documents[0])] == [0, 1]
    assert all(chunk.source_label.endswith(f"#chunk-{chunk.chunk_index}") for chunk in chunks)


def test_extracts_tenant_isolation_fact(tmp_path):
    facts = extract_facts_from_chunks(load_sample_chunks(tmp_path))

    tenant_fact = next(fact for fact in facts if fact.category == "tenant_isolation")
    assert "tenant_id" in tenant_fact.evidence_quote
    assert tenant_fact.source_document == "architecture.md"


def test_extracts_model_training_fact(tmp_path):
    facts = extract_facts_from_chunks(load_sample_chunks(tmp_path))

    training_fact = next(fact for fact in facts if fact.category == "model_training")
    assert training_fact.claim == "Customer prompts are not used for model training."
    assert training_fact.evidence_quote == training_fact.claim
    assert training_fact.polarity is FactPolarity.NEGATIVE


def test_does_not_extract_soc2_when_missing(tmp_path):
    facts = extract_facts_from_chunks(load_sample_chunks(tmp_path))

    assert not any(fact.category == "soc2" for fact in facts)


def test_each_fact_has_source_evidence(tmp_path):
    chunks = load_sample_chunks(tmp_path)
    chunks_by_id = {chunk.id: chunk for chunk in chunks}

    facts = extract_facts_from_chunks(chunks)

    assert facts
    for fact in facts:
        assert fact.evidence_quote
        assert fact.source_document
        assert fact.source_chunk_id in chunks_by_id
        assert fact.evidence_quote in chunks_by_id[fact.source_chunk_id].text
        assert 0.0 <= fact.confidence <= 1.0
        assert fact.review_status is FactReviewStatus.APPROVED


def test_recognizes_each_supported_fact_category(tmp_path):
    (tmp_path / "controls.md").write_text(
        """Queries enforce tenant isolation.
Data uses encryption at rest.
Customer data is not used for model training.
Prompts are retained for seven days.
Administrative actions produce audit logs.
Privileged access requires approval.
The incident response plan is reviewed annually.
The company completed SOC 2 Type II.
The service documents HIPAA compliance.
The team performs prompt injection testing.
""",
        encoding="utf-8",
    )
    document = load_documents_from_directory(tmp_path)[0]

    facts = extract_facts_from_chunks(chunk_document(document))

    assert {fact.category for fact in facts} == {
        "tenant_isolation",
        "encryption",
        "model_training",
        "prompt_retention",
        "audit_logging",
        "admin_access",
        "incident_response",
        "soc2",
        "hipaa",
        "prompt_injection_testing",
    }


def test_assigns_polarity_relative_to_canonical_proposition(tmp_path):
    (tmp_path / "soc2.md").write_text(
        "We have not completed a SOC 2 Type II audit.\n\n"
        "SOC 2 Type II is listed on the roadmap.",
        encoding="utf-8",
    )
    document = load_documents_from_directory(tmp_path)[0]

    facts = extract_facts_from_chunks(chunk_document(document))

    assert [fact.polarity for fact in facts] == [
        FactPolarity.NEGATIVE,
        FactPolarity.NEUTRAL,
    ]


def test_does_not_treat_every_not_as_negative(tmp_path):
    (tmp_path / "encryption.md").write_text(
        "Customer data is not only encrypted at rest, but also backed up.",
        encoding="utf-8",
    )
    document = load_documents_from_directory(tmp_path)[0]

    fact = extract_facts_from_chunks(chunk_document(document))[0]

    assert fact.polarity is FactPolarity.POSITIVE


def test_assigns_explicit_control_scoped_applicability(tmp_path):
    (tmp_path / "applicability.md").write_text(
        "Encryption at rest is not applicable to this stateless component.\n\n"
        "Encryption at rest is enabled; automatic key rotation is not applicable.",
        encoding="utf-8",
    )
    document = load_documents_from_directory(tmp_path)[0]

    facts = extract_facts_from_chunks(chunk_document(document))

    assert facts[0].applicability is FactApplicability.NOT_APPLICABLE
    assert facts[0].polarity is FactPolarity.NEUTRAL
    assert facts[1].applicability is FactApplicability.APPLICABLE
    assert facts[1].polarity is FactPolarity.POSITIVE
