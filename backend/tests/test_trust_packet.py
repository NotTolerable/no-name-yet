import json
import pytest

from core.models import PolicyStatus, TrustPacket
from core.trust_packet import generate_trust_packet


def build_sample_inputs(tmp_path):
    docs_path = tmp_path / "docs"
    docs_path.mkdir()
    (docs_path / "architecture.md").write_text(
        """# Architecture

All customer records include a tenant_id and queries are scoped by authenticated tenant.

Customer prompts are not used for model training.
""",
        encoding="utf-8",
    )

    questionnaire_path = tmp_path / "questionnaire.json"
    questionnaire_path.write_text(
        json.dumps(
            {
                "questions": [
                    {
                        "id": "q-tenant",
                        "question_text": "Do you isolate customer data by tenant?",
                        "required_control": "tenant_isolation",
                        "risk_domain": "security",
                        "response_kind": "BINARY",
                        "affirmative_polarity": "POSITIVE",
                    },
                    {
                        "id": "q-training",
                        "question_text": "Do you use customer prompts for model training?",
                        "required_control": "model_training",
                        "risk_domain": "ai_governance",
                        "response_kind": "BINARY",
                        "affirmative_polarity": "POSITIVE",
                    },
                    {
                        "id": "q-soc2",
                        "question_text": "Are you SOC 2 Type II compliant?",
                        "required_control": "soc2_type_ii",
                        "risk_domain": "compliance",
                        "response_kind": "BINARY",
                        "affirmative_polarity": "POSITIVE",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    return docs_path, questionnaire_path


def generate_sample_packet(tmp_path):
    docs_path, questionnaire_path = build_sample_inputs(tmp_path)
    return generate_trust_packet(str(docs_path), str(questionnaire_path))


def test_generates_trust_packet(tmp_path):
    packet = generate_sample_packet(tmp_path)

    assert isinstance(packet, TrustPacket)
    assert len(packet.answers) == 3
    assert packet.summary == "Processed 3 questions: 2 supported, 0 partial, and 1 deficits."


def test_packet_contains_supported_answers(tmp_path):
    packet = generate_sample_packet(tmp_path)

    supported_ids = {
        answer.question_id
        for answer in packet.answers
        if answer.status is PolicyStatus.SUPPORTED
    }
    assert supported_ids == {"q-tenant", "q-training"}


def test_packet_contains_deficits(tmp_path):
    packet = generate_sample_packet(tmp_path)

    deficits = [
        answer for answer in packet.answers if answer.status is PolicyStatus.DEFICIT
    ]
    assert [answer.question_id for answer in deficits] == ["q-soc2"]


def test_soc2_is_deficit_when_no_evidence(tmp_path):
    packet = generate_sample_packet(tmp_path)
    soc2_answer = next(
        answer for answer in packet.answers if answer.question_id == "q-soc2"
    )

    assert soc2_answer.status is PolicyStatus.DEFICIT
    assert soc2_answer.citations == []


def test_supported_answers_have_citations(tmp_path):
    packet = generate_sample_packet(tmp_path)

    supported_answers = [
        answer for answer in packet.answers if answer.status is PolicyStatus.SUPPORTED
    ]
    assert supported_answers
    assert all(answer.citations for answer in supported_answers)


def test_buyer_packet_does_not_include_unsupported_positive_claims(tmp_path):
    packet = generate_sample_packet(tmp_path)
    soc2_answer = next(
        answer for answer in packet.answers if answer.question_id == "q-soc2"
    )

    assert "SOC 2 Type II compliant" not in soc2_answer.answer_text
    assert "No evidence-backed answer was generated" in soc2_answer.answer_text


def test_remediation_tasks_exist_for_deficits(tmp_path):
    packet = generate_sample_packet(tmp_path)
    deficit_ids = {
        answer.question_id
        for answer in packet.answers
        if answer.status is PolicyStatus.DEFICIT
    }

    assert {task.question_id for task in packet.remediation_tasks} == deficit_ids


def test_questionnaire_rejects_missing_response_metadata(tmp_path):
    docs_path = tmp_path / "docs"
    docs_path.mkdir()
    (docs_path / "architecture.md").write_text(
        "Customer data is encrypted at rest.", encoding="utf-8"
    )
    questionnaire_path = tmp_path / "invalid-questionnaire.json"
    questionnaire_path.write_text(
        json.dumps(
            {
                "questions": [
                    {
                        "id": "q-missing-metadata",
                        "question_text": "Is customer data encrypted at rest?",
                        "required_control": "encryption_at_rest",
                        "risk_domain": "security",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid questionnaire item"):
        generate_trust_packet(str(docs_path), str(questionnaire_path))
