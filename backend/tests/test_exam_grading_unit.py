import pytest

from app.modules.executions.domain.exceptions import ExecutionInputLimitError
from app.modules.executions.domain.trace import TraceExecutionResult
from app.modules.exams.application.services.exam_grading_service import ExamGradingService


pytestmark = pytest.mark.no_db


class FakeExamService:
    def get_assessment_definition(self, lesson_id: str) -> dict[str, object]:
        return {
            "question_id": f"question-{lesson_id}",
            "function_name": "solve",
            "test_cases": [{"id": "case-1", "args": [], "expected": 1}],
        }


class FakeRunner:
    def __init__(self, result: TraceExecutionResult | None = None) -> None:
        self.result = result or TraceExecutionResult.from_payload(
            language="python",
            payload={
                "status": "completed",
                "stdout": (
                    '{"status":"passed","passedCount":1,"totalCount":1,'
                    '"errorMessage":null,"results":[]}'
                ),
                "stderr": "",
                "steps": [],
            },
        )

    def run(self, command):
        return self.result


def test_exam_grading_rejects_oversized_source_code(monkeypatch):
    monkeypatch.setattr(
        "app.modules.exams.application.services.exam_grading_service.settings.runner_max_source_code_chars",
        3,
    )
    service = ExamGradingService(exam_service=FakeExamService(), runner=FakeRunner())

    with pytest.raises(ExecutionInputLimitError):
        service.grade_submission(lesson_id="lesson-1", source_code="def solve():\n    return 1\n")


def test_exam_grading_script_uses_bounded_stdout():
    service = ExamGradingService(exam_service=FakeExamService(), runner=FakeRunner())

    script = service._build_grading_script(
        source_code="def solve():\n    print('x' * 100)\n    return 1\n",
        function_name="solve",
        test_cases=[{"id": "case-1", "args": [], "expected": 1}],
        max_stdout_chars=10,
    )

    assert "class BoundedStdout" in script
    assert "MAX_STDOUT_CHARS = 10" in script
