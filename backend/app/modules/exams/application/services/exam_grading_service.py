import json

from app.common.text_validation import ensure_utf8_encodable
from app.core.config import settings
from app.modules.exams.application.services.exam_service import ExamService
from app.modules.exams.presentation.http.schemas import (
    ExamCaseResultRead,
    ExamSubmissionRead,
)
from app.modules.executions.domain.exceptions import ExecutionInputLimitError
from app.modules.executions.domain.ports import TraceRunnerProtocol
from app.modules.executions.domain.trace import TraceExecutionCommand
from app.modules.executions.shared.language_detection import get_language_mismatch_message


class ExamGradingService:
    def __init__(
        self,
        *,
        exam_service: ExamService,
        runner: TraceRunnerProtocol,
    ) -> None:
        self._exam_service = exam_service
        self._runner = runner

    def grade_submission(
        self,
        *,
        lesson_id: str,
        source_code: str,
        language: str = "python",
    ) -> ExamSubmissionRead:
        if len(source_code) > settings.runner_max_source_code_chars:
            raise ExecutionInputLimitError("제출 코드 길이가 허용 범위를 초과했습니다.")

        try:
            ensure_utf8_encodable(source_code, field_label="제출 코드")
        except ValueError as error:
            raise ExecutionInputLimitError(str(error)) from error

        assessment = self._exam_service.get_assessment_definition(lesson_id)
        test_cases = assessment["test_cases"]

        language_mismatch_message = get_language_mismatch_message(
            selected_language=language,
            source_code=source_code,
        )
        if language_mismatch_message is not None:
            return ExamSubmissionRead(
                lesson_id=lesson_id,
                question_id=str(assessment["question_id"]),
                status="error",
                score=0,
                passed_count=0,
                total_count=len(test_cases),
                error_message=language_mismatch_message,
                results=[],
            )

        if language != "python":
            return ExamSubmissionRead(
                lesson_id=lesson_id,
                question_id=str(assessment["question_id"]),
                status="error",
                score=0,
                passed_count=0,
                total_count=len(test_cases),
                error_message=(
                    "현재 시험 채점은 Python 함수형 답안만 지원합니다. "
                    "C/Java 코드는 실행 추적에서 검증하세요."
                ),
                results=[],
            )

        execution_result = self._runner.run(
            TraceExecutionCommand(
                language=language,
                source_code=self._build_grading_script(
                    source_code=source_code,
                    function_name=str(assessment["function_name"]),
                    test_cases=test_cases,
                    max_stdout_chars=settings.runner_max_stdout_chars,
                ),
                stdin="",
            )
        )

        if execution_result.status == "timeout":
            return ExamSubmissionRead(
                lesson_id=lesson_id,
                question_id=str(assessment["question_id"]),
                status="timeout",
                score=0,
                passed_count=0,
                total_count=len(test_cases),
                error_message=execution_result.error_message or "채점 시간이 제한을 초과했습니다.",
                results=[],
            )

        if execution_result.status != "completed":
            return ExamSubmissionRead(
                lesson_id=lesson_id,
                question_id=str(assessment["question_id"]),
                status="error",
                score=0,
                passed_count=0,
                total_count=len(test_cases),
                error_message=(
                    execution_result.error_message
                    or execution_result.stderr
                    or "채점에 실패했습니다."
                ),
                results=[],
            )

        try:
            payload = json.loads(execution_result.stdout or "{}")
        except json.JSONDecodeError:
            return ExamSubmissionRead(
                lesson_id=lesson_id,
                question_id=str(assessment["question_id"]),
                status="error",
                score=0,
                passed_count=0,
                total_count=len(test_cases),
                error_message="채점 결과를 해석하지 못했습니다.",
                results=[],
            )

        total_count = int(payload.get("totalCount", len(test_cases)))
        passed_count = int(payload.get("passedCount", 0))
        score = 0 if total_count == 0 else round((passed_count / total_count) * 100)
        results = [
            ExamCaseResultRead.model_validate(item)
            for item in payload.get("results", [])
        ]

        return ExamSubmissionRead(
            lesson_id=lesson_id,
            question_id=str(assessment["question_id"]),
            status=payload.get("status", "error"),
            score=score,
            passed_count=passed_count,
            total_count=total_count,
            error_message=payload.get("errorMessage"),
            results=results,
        )

    def _build_grading_script(
        self,
        *,
        source_code: str,
        function_name: str,
        test_cases: list[dict[str, object]],
        max_stdout_chars: int,
    ) -> str:
        return f"""
import contextlib
import copy
import io
import json

USER_SOURCE = {source_code!r}
FUNCTION_NAME = {function_name!r}
TEST_CASES = {test_cases!r}
MAX_STDOUT_CHARS = {max_stdout_chars!r}


class BoundedStdout(io.TextIOBase):
    def __init__(self, max_chars):
        self._max_chars = max_chars
        self._buffer = io.StringIO()
        self.truncated = False

    def write(self, data):
        if self.truncated:
            return len(data)

        remaining = self._max_chars - self._buffer.tell()
        if remaining <= 0:
            self.truncated = True
            return len(data)

        self._buffer.write(data[:remaining])
        if len(data) > remaining:
            self.truncated = True
        return len(data)

    def getvalue(self):
        return self._buffer.getvalue()


def normalize(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, tuple):
        return [normalize(item) for item in value]
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {{str(key): normalize(item) for key, item in value.items()}}
    if isinstance(value, set):
        return sorted(normalize(item) for item in value)
    return repr(value)


def print_result(payload):
    print(json.dumps(payload, ensure_ascii=False))


namespace = {{}}
bootstrap_stdout = BoundedStdout(MAX_STDOUT_CHARS)

try:
    with contextlib.redirect_stdout(bootstrap_stdout):
        exec(USER_SOURCE, namespace, namespace)
except Exception as error:
    print_result(
        {{
            "status": "error",
            "passedCount": 0,
            "totalCount": len(TEST_CASES),
            "errorMessage": f"{{type(error).__name__}}: {{error}}",
            "results": [],
        }}
    )
    raise SystemExit

target = namespace.get(FUNCTION_NAME)
if not callable(target):
    print_result(
        {{
            "status": "error",
            "passedCount": 0,
            "totalCount": len(TEST_CASES),
            "errorMessage": f"함수 '{{FUNCTION_NAME}}'를 찾을 수 없습니다.",
            "results": [],
        }}
    )
    raise SystemExit

results = []
passed_count = 0

for case in TEST_CASES:
    raw_args = case.get("args", [])
    raw_kwargs = case.get("kwargs", {{}})
    args = copy.deepcopy(raw_args)
    kwargs = copy.deepcopy(raw_kwargs)
    input_summary = f"args={{raw_args}}, kwargs={{raw_kwargs}}"
    expected = normalize(case.get("expected"))
    expected_stdout = case.get("expected_stdout")
    captured_stdout = BoundedStdout(MAX_STDOUT_CHARS)

    try:
        with contextlib.redirect_stdout(captured_stdout):
            actual_value = target(*args, **kwargs)
        actual_error = None
    except Exception as error:
        actual_value = None
        actual_error = f"{{type(error).__name__}}: {{error}}"

    actual = normalize(actual_value)
    actual_stdout = captured_stdout.getvalue()
    stdout_truncated = captured_stdout.truncated
    passed = actual_error is None and actual == expected and not stdout_truncated

    if expected_stdout is not None:
        passed = passed and not stdout_truncated and actual_stdout == expected_stdout

    if passed:
        message = "통과"
        passed_count += 1
    elif stdout_truncated:
        message = "stdout 출력이 제한 길이를 초과해 잘렸습니다."
    elif actual_error is not None:
        message = actual_error
    else:
        message = "반환값이 예상과 다릅니다."

    results.append(
        {{
            "caseId": case["id"],
            "passed": passed,
            "inputSummary": input_summary,
            "expected": expected,
            "actual": actual if actual_error is None else actual_error,
            "message": message,
        }}
    )

status = "passed" if passed_count == len(TEST_CASES) else "failed"
print_result(
    {{
        "status": status,
        "passedCount": passed_count,
        "totalCount": len(TEST_CASES),
        "errorMessage": None,
        "results": results,
    }}
)
"""
