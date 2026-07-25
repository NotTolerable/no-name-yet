"""FastAPI application for the deterministic Verilly demo pipeline."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.models import FactPolarity, Question, QuestionResponseKind, TrustPacket
from core.fact_graph import (
    chunk_document,
    extract_facts_from_chunks,
    load_documents_from_directory,
)
from core.trust_packet import generate_trust_packet
from database import RunRepository, create_database_client_from_env


class HealthResponse(BaseModel):
    status: str


class DemoDocument(BaseModel):
    file_name: str
    text: str


DEMO_DOCUMENTS = [
    DemoDocument(
        file_name="architecture.md",
        text=(
            "# Architecture\n\n"
            "All customer records include a tenant_id and queries are scoped "
            "by authenticated tenant.\n\n"
            "Administrative changes are recorded in audit logs.\n"
        ),
    ),
    DemoDocument(
        file_name="ai-policy.txt",
        text=(
            "Customer prompts are not used for model training.\n\n"
            "Prompts are retained for 30 days.\n"
        ),
    ),
]

DEMO_QUESTIONS = [
    Question(
        id="q-tenant",
        question_text="Do you isolate customer data by tenant?",
        required_control="tenant_isolation",
        risk_domain="security",
        response_kind=QuestionResponseKind.BINARY,
        affirmative_polarity=FactPolarity.POSITIVE,
    ),
    Question(
        id="q-training",
        question_text="Do you use customer prompts for model training?",
        required_control="model_training",
        risk_domain="ai_governance",
        response_kind=QuestionResponseKind.BINARY,
        affirmative_polarity=FactPolarity.POSITIVE,
    ),
    Question(
        id="q-soc2",
        question_text="Are you SOC 2 Type II compliant?",
        required_control="soc2_type_ii",
        risk_domain="compliance",
        response_kind=QuestionResponseKind.BINARY,
        affirmative_polarity=FactPolarity.POSITIVE,
    ),
    Question(
        id="q-hipaa",
        question_text="Are you HIPAA compliant?",
        required_control="hipaa_compliance",
        risk_domain="compliance",
        response_kind=QuestionResponseKind.BINARY,
        affirmative_polarity=FactPolarity.POSITIVE,
    ),
]


app = FastAPI(title="Verilly API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/demo/questionnaire", response_model=list[Question])
def demo_questionnaire() -> list[Question]:
    return DEMO_QUESTIONS


@app.get("/demo/docs", response_model=list[DemoDocument])
def demo_docs() -> list[DemoDocument]:
    return DEMO_DOCUMENTS


def _run_repository() -> RunRepository | None:
    database = create_database_client_from_env()
    return RunRepository(database) if database is not None else None


@app.post("/runs/demo", response_model=TrustPacket)
def run_demo(response: Response) -> TrustPacket:
    with TemporaryDirectory(prefix="verilly-demo-") as temporary_directory:
        root = Path(temporary_directory)
        docs_path = root / "docs"
        docs_path.mkdir()
        for document in DEMO_DOCUMENTS:
            (docs_path / document.file_name).write_text(
                document.text, encoding="utf-8"
            )

        questionnaire_path = root / "questionnaire.json"
        questionnaire_path.write_text(
            json.dumps(
                {"questions": [question.model_dump() for question in DEMO_QUESTIONS]}
            ),
            encoding="utf-8",
        )
        packet = generate_trust_packet(str(docs_path), str(questionnaire_path))

        repository = _run_repository()
        if repository is not None:
            documents = load_documents_from_directory(docs_path)
            chunks = [
                chunk
                for document in documents
                for chunk in chunk_document(document)
            ]
            facts = extract_facts_from_chunks(chunks)
            run_id = repository.save_run(
                project_name="Verilly demo",
                documents=documents,
                chunks=chunks,
                facts=facts,
                questions=DEMO_QUESTIONS,
                packet=packet,
            )
            response.headers["X-Verilly-Run-ID"] = run_id
        return packet


@app.get("/runs/{run_id}", response_model=TrustPacket)
def get_saved_run(run_id: str) -> TrustPacket:
    repository = _run_repository()
    if repository is None:
        raise HTTPException(status_code=503, detail="Supabase persistence is not configured")
    try:
        return repository.load_run(run_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Run not found") from error
