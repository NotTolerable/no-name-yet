from core.deficit_generator import generate_remediation_task
from core.models import (
    AnswerValue,
    FactPolarity,
    PolicyDecision,
    PolicyStatus,
    Question,
    QuestionResponseKind,
)


def make_soc2_question():
    return Question(
        id="q-soc2",
        question_text="Are you SOC 2 Type II compliant?",
        required_control="soc2_type_ii",
        risk_domain="compliance",
        response_kind=QuestionResponseKind.BINARY,
        affirmative_polarity=FactPolarity.POSITIVE,
    )


def make_decision(status=PolicyStatus.DEFICIT):
    return PolicyDecision(
        question_id="q-soc2",
        status=status,
        answer_value=(
            AnswerValue.UNKNOWN
            if status is PolicyStatus.DEFICIT
            else AnswerValue.YES
        ),
        response_kind=QuestionResponseKind.BINARY,
        reason="No explicit SOC 2 Type II evidence was found.",
        cited_fact_ids=[] if status is PolicyStatus.DEFICIT else ["fact-soc2"],
    )


def test_soc2_deficit_generates_remediation_task():
    task = generate_remediation_task(make_soc2_question(), make_decision())

    assert task is not None
    assert task.question_id == "q-soc2"
    assert "soc2 type ii" in task.title.lower()
    assert "before making a buyer-facing claim" in task.description


def test_remediation_task_has_title_description_severity():
    task = generate_remediation_task(make_soc2_question(), make_decision())

    assert task is not None
    assert task.title
    assert task.description
    assert task.severity == "high"


def test_non_deficit_does_not_generate_remediation_task():
    task = generate_remediation_task(
        make_soc2_question(), make_decision(PolicyStatus.SUPPORTED)
    )

    assert task is None
