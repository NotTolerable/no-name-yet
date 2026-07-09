from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_run_returns_trust_packet():
    response = client.post("/runs/demo")

    assert response.status_code == 200
    packet = response.json()
    assert set(packet) == {"answers", "remediation_tasks", "summary"}
    assert len(packet["answers"]) == 4


def test_demo_run_contains_supported_and_deficit_items():
    packet = client.post("/runs/demo").json()
    statuses = {answer["status"] for answer in packet["answers"]}

    assert "SUPPORTED" in statuses
    assert "DEFICIT" in statuses


def test_demo_run_does_not_claim_soc2():
    packet = client.post("/runs/demo").json()
    soc2_answer = next(
        answer for answer in packet["answers"] if answer["question_id"] == "q-soc2"
    )

    assert soc2_answer["status"] == "DEFICIT"
    assert soc2_answer["citations"] == []
    assert "SOC 2 Type II compliant" not in soc2_answer["answer_text"]
    assert "No evidence-backed answer was generated" in soc2_answer["answer_text"]


def test_demo_fixture_endpoints():
    questionnaire_response = client.get("/demo/questionnaire")
    docs_response = client.get("/demo/docs")

    assert questionnaire_response.status_code == 200
    assert docs_response.status_code == 200
    assert any(item["id"] == "q-soc2" for item in questionnaire_response.json())
    assert {item["file_name"] for item in docs_response.json()} == {
        "ai-policy.txt",
        "architecture.md",
    }
