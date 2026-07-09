"""End-to-end deterministic trust packet pipeline."""

import csv
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from core.answer_generator import generate_answer
from core.deficit_generator import generate_remediation_task
from core.evidence_matcher import match_question_to_facts
from core.fact_graph import (
    chunk_document,
    extract_facts_from_chunks,
    load_documents_from_directory,
)
from core.models import Fact, PolicyStatus, Question, TrustPacket
from core.policy import evaluate_question_policy


POLICY_MATCH_THRESHOLD = 0.5


def _question_from_mapping(data: dict[str, Any], index: int) -> Question:
    normalized = dict(data)
    if "question_text" not in normalized and "question" in normalized:
        normalized["question_text"] = normalized.pop("question")
    try:
        return Question.model_validate(normalized)
    except ValidationError as error:
        raise ValueError(f"Invalid questionnaire item at index {index}: {error}") from error


def _load_questionnaire(path: str | Path) -> list[Question]:
    questionnaire_path = Path(path)
    if not questionnaire_path.is_file():
        raise ValueError(f"Questionnaire file does not exist: {questionnaire_path}")

    suffix = questionnaire_path.suffix.lower()
    if suffix == ".json":
        try:
            payload = json.loads(questionnaire_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"Questionnaire is not valid JSON: {error}") from error
        if isinstance(payload, dict):
            payload = payload.get("questions")
        if not isinstance(payload, list):
            raise ValueError("JSON questionnaire must be a list or contain 'questions'")
        rows = payload
    elif suffix == ".csv":
        with questionnaire_path.open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
    else:
        raise ValueError("Questionnaire must be a .json or .csv file")

    questions: list[Question] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Questionnaire item at index {index} must be an object")
        questions.append(_question_from_mapping(row, index))
    return questions


def _policy_eligible_facts(
    question: Question, facts: list[Fact]
) -> list[Fact]:
    matches = match_question_to_facts(question, facts)
    eligible_ids = {
        match.fact_id
        for match in matches
        if match.relevance >= POLICY_MATCH_THRESHOLD
    }
    return [fact for fact in facts if fact.id in eligible_ids]


def generate_trust_packet(docs_path: str, questionnaire_path: str) -> TrustPacket:
    """Run the verification pipeline and return reviewable answers and deficits."""

    documents = load_documents_from_directory(docs_path)
    chunks = [
        chunk
        for document in documents
        for chunk in chunk_document(document)
    ]
    facts = extract_facts_from_chunks(chunks)
    questions = _load_questionnaire(questionnaire_path)

    answers = []
    remediation_tasks = []
    for question in questions:
        matching_facts = _policy_eligible_facts(question, facts)
        decision = evaluate_question_policy(question, matching_facts)
        answers.append(generate_answer(question, decision, matching_facts))

        remediation_task = generate_remediation_task(question, decision)
        if remediation_task is not None:
            remediation_tasks.append(remediation_task)

    supported_count = sum(
        answer.status is PolicyStatus.SUPPORTED for answer in answers
    )
    partial_count = sum(answer.status is PolicyStatus.PARTIAL for answer in answers)
    deficit_count = sum(answer.status is PolicyStatus.DEFICIT for answer in answers)
    summary = (
        f"Processed {len(questions)} questions: {supported_count} supported, "
        f"{partial_count} partial, and {deficit_count} deficits."
    )

    return TrustPacket(
        answers=answers,
        remediation_tasks=remediation_tasks,
        summary=summary,
    )
