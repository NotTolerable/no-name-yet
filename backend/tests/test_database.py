import json

from core.fact_graph import (
    chunk_document,
    extract_facts_from_chunks,
    load_documents_from_directory,
)
from core.models import Question
from core.trust_packet import generate_trust_packet
from database import RunRepository


class InMemoryDatabase:
    def __init__(self):
        self.tables = {
            table: []
            for table in (
                "projects",
                "runs",
                "documents",
                "document_chunks",
                "facts",
                "questions",
                "answers",
                "remediation_tasks",
            )
        }

    def insert(self, table, rows):
        self.tables[table].extend(dict(row) for row in rows)

    def select(self, table, filters):
        return [
            dict(row)
            for row in self.tables[table]
            if all(row.get(key) == value for key, value in filters.items())
        ]


def build_run_inputs(tmp_path):
    docs_path = tmp_path / "docs"
    docs_path.mkdir()
    (docs_path / "architecture.md").write_text(
        "All records include tenant_id and queries are scoped by authenticated tenant.",
        encoding="utf-8",
    )
    questions = [
        Question(
            id="q-tenant",
            question_text="Do you isolate customer data by tenant?",
            required_control="tenant_isolation",
            risk_domain="security",
        ),
        Question(
            id="q-soc2",
            question_text="Are you SOC 2 Type II compliant?",
            required_control="soc2_type_ii",
            risk_domain="compliance",
        ),
    ]
    questionnaire_path = tmp_path / "questions.json"
    questionnaire_path.write_text(
        json.dumps({"questions": [question.model_dump() for question in questions]}),
        encoding="utf-8",
    )
    documents = load_documents_from_directory(docs_path)
    chunks = [
        chunk for document in documents for chunk in chunk_document(document)
    ]
    facts = extract_facts_from_chunks(chunks)
    packet = generate_trust_packet(str(docs_path), str(questionnaire_path))
    return documents, chunks, facts, questions, packet


def save_sample_run(tmp_path):
    database = InMemoryDatabase()
    repository = RunRepository(database)
    documents, chunks, facts, questions, packet = build_run_inputs(tmp_path)
    run_id = repository.save_run(
        project_name="Test project",
        documents=documents,
        chunks=chunks,
        facts=facts,
        questions=questions,
        packet=packet,
    )
    return database, repository, run_id, packet


def test_run_can_be_saved(tmp_path):
    database, _, run_id, _ = save_sample_run(tmp_path)

    assert database.tables["runs"][0]["id"] == run_id
    assert database.tables["runs"][0]["status"] == "completed"
    assert len(database.tables["answers"]) == 2


def test_saved_run_can_be_loaded(tmp_path):
    _, repository, run_id, original_packet = save_sample_run(tmp_path)

    loaded_packet = repository.load_run(run_id)

    assert loaded_packet.model_dump() == original_packet.model_dump()


def test_citations_reference_saved_facts(tmp_path):
    database, _, _, _ = save_sample_run(tmp_path)
    saved_fact_ids = {fact["id"] for fact in database.tables["facts"]}
    supported_answer = next(
        answer
        for answer in database.tables["answers"]
        if answer["status"] == "SUPPORTED"
    )

    assert supported_answer["cited_fact_ids"]
    assert set(supported_answer["cited_fact_ids"]) <= saved_fact_ids


def test_deficits_reference_saved_questions(tmp_path):
    database, _, _, _ = save_sample_run(tmp_path)
    saved_question_ids = {question["id"] for question in database.tables["questions"]}
    deficit_question_ids = {
        answer["question_id"]
        for answer in database.tables["answers"]
        if answer["status"] == "DEFICIT"
    }
    task_question_ids = {
        task["question_id"] for task in database.tables["remediation_tasks"]
    }

    assert deficit_question_ids
    assert deficit_question_ids == task_question_ids
    assert deficit_question_ids <= saved_question_ids
