"""Backend-only Supabase persistence for governed verification runs."""

from collections.abc import Mapping
import os
import re
from typing import Any, Protocol
from uuid import uuid4

import httpx

from core.models import (
    Answer,
    Document,
    DocumentChunk,
    Fact,
    Question,
    RemediationTask,
    TrustPacket,
)


class DatabaseBackend(Protocol):
    def insert(self, table: str, rows: list[dict[str, Any]]) -> None: ...

    def select(
        self, table: str, filters: Mapping[str, Any]
    ) -> list[dict[str, Any]]: ...


class SupabaseDatabaseClient:
    """Minimal PostgREST client that never leaves backend process boundaries."""

    def __init__(self, url: str, service_role_key: str) -> None:
        self._client = httpx.Client(
            base_url=f"{url.rstrip('/')}/rest/v1",
            headers={
                "apikey": service_role_key,
                "Authorization": f"Bearer {service_role_key}",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )

    def insert(self, table: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        response = self._client.post(
            f"/{table}",
            json=rows,
            headers={"Prefer": "return=minimal"},
        )
        response.raise_for_status()

    def select(
        self, table: str, filters: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        params = {"select": "*"}
        params.update({key: f"eq.{value}" for key, value in filters.items()})
        response = self._client.get(f"/{table}", params=params)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError(f"Unexpected Supabase response for table {table}")
        return payload


def create_database_client_from_env() -> SupabaseDatabaseClient | None:
    url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url and not service_role_key:
        return None
    if not url or not service_role_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured together"
        )
    return SupabaseDatabaseClient(url, service_role_key)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "project"


class RunRepository:
    def __init__(self, database: DatabaseBackend) -> None:
        self.database = database

    def _project_id(self, project_name: str) -> str:
        slug = _slugify(project_name)
        existing = self.database.select("projects", {"slug": slug})
        if existing:
            return str(existing[0]["id"])

        project_id = str(uuid4())
        self.database.insert(
            "projects",
            [{"id": project_id, "slug": slug, "name": project_name}],
        )
        return project_id

    def save_run(
        self,
        *,
        project_name: str,
        documents: list[Document],
        chunks: list[DocumentChunk],
        facts: list[Fact],
        questions: list[Question],
        packet: TrustPacket,
    ) -> str:
        project_id = self._project_id(project_name)
        run_id = str(uuid4())
        self.database.insert(
            "runs",
            [
                {
                    "id": run_id,
                    "project_id": project_id,
                    "status": "completed",
                    "summary": packet.summary,
                }
            ],
        )

        document_ids = {document.id: str(uuid4()) for document in documents}
        self.database.insert(
            "documents",
            [
                {
                    "id": document_ids[document.id],
                    "run_id": run_id,
                    "source_document_id": document.id,
                    "file_name": document.file_name,
                    "content": document.text,
                }
                for document in documents
            ],
        )

        chunk_ids = {chunk.id: str(uuid4()) for chunk in chunks}
        self.database.insert(
            "document_chunks",
            [
                {
                    "id": chunk_ids[chunk.id],
                    "run_id": run_id,
                    "document_id": document_ids[chunk.document_id],
                    "source_chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "source_label": chunk.source_label,
                }
                for chunk in chunks
            ],
        )

        fact_ids = {fact.id: str(uuid4()) for fact in facts}
        self.database.insert(
            "facts",
            [
                {
                    "id": fact_ids[fact.id],
                    "run_id": run_id,
                    "document_chunk_id": chunk_ids[fact.source_chunk_id],
                    "source_fact_id": fact.id,
                    "category": fact.category,
                    "claim": fact.claim,
                    "evidence_quote": fact.evidence_quote,
                    "source_document": fact.source_document,
                    "confidence": fact.confidence,
                }
                for fact in facts
            ],
        )

        question_ids = {question.id: str(uuid4()) for question in questions}
        self.database.insert(
            "questions",
            [
                {
                    "id": question_ids[question.id],
                    "run_id": run_id,
                    "source_question_id": question.id,
                    "position": position,
                    "question_text": question.question_text,
                    "required_control": question.required_control,
                    "risk_domain": question.risk_domain,
                }
                for position, question in enumerate(questions)
            ],
        )

        facts_by_quote: dict[str, list[str]] = {}
        for fact in facts:
            facts_by_quote.setdefault(fact.evidence_quote, []).append(fact_ids[fact.id])

        self.database.insert(
            "answers",
            [
                {
                    "id": str(uuid4()),
                    "run_id": run_id,
                    "question_id": question_ids[answer.question_id],
                    "position": position,
                    "status": answer.status.value,
                    "answer_text": answer.answer_text,
                    "policy_reason": answer.policy_reason,
                    "citations": answer.citations,
                    "cited_fact_ids": [
                        fact_id
                        for citation in answer.citations
                        for fact_id in facts_by_quote.get(citation, [])
                    ],
                }
                for position, answer in enumerate(packet.answers)
            ],
        )

        self.database.insert(
            "remediation_tasks",
            [
                {
                    "id": str(uuid4()),
                    "run_id": run_id,
                    "question_id": question_ids[task.question_id],
                    "title": task.title,
                    "description": task.description,
                    "severity": task.severity,
                    "suggested_owner": task.suggested_owner,
                }
                for task in packet.remediation_tasks
            ],
        )
        return run_id

    def load_run(self, run_id: str) -> TrustPacket:
        runs = self.database.select("runs", {"id": run_id})
        if not runs:
            raise KeyError(run_id)

        question_rows = self.database.select("questions", {"run_id": run_id})
        question_source_ids = {
            str(row["id"]): str(row["source_question_id"]) for row in question_rows
        }
        answer_rows = sorted(
            self.database.select("answers", {"run_id": run_id}),
            key=lambda row: int(row["position"]),
        )
        task_rows = self.database.select("remediation_tasks", {"run_id": run_id})

        answers = [
            Answer(
                question_id=question_source_ids[str(row["question_id"])],
                status=str(row["status"]),
                answer_text=str(row["answer_text"]),
                citations=list(row["citations"]),
                policy_reason=str(row["policy_reason"]),
            )
            for row in answer_rows
        ]
        remediation_tasks = [
            RemediationTask(
                question_id=question_source_ids[str(row["question_id"])],
                title=str(row["title"]),
                description=str(row["description"]),
                severity=str(row["severity"]),
                suggested_owner=str(row["suggested_owner"]),
            )
            for row in task_rows
        ]
        return TrustPacket(
            answers=answers,
            remediation_tasks=remediation_tasks,
            summary=str(runs[0]["summary"]),
        )
