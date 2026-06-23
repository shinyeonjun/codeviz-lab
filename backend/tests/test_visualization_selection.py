import json

import httpx

from app.modules.executions.domain.trace import TraceExecutionResult
from app.modules.executions.selection.base.schemas import VisualizationSelectionContext
from app.modules.executions.selection.providers.manual_selector import ManualVisualizationSelector
from app.modules.executions.selection.providers.openai_selector import OpenAIVisualizationSelector


def test_manual_selector_returns_default_mode_for_auto_request():
    selector = ManualVisualizationSelector(
        supported_modes={"none", "array-bars", "call-stack"},
        default_mode="none",
    )

    result = selector.select(
        VisualizationSelectionContext(
            requested_mode="auto",
            source_code="print('hello')",
            language="python",
        )
    )

    assert result.selected_mode == "none"
    assert result.confidence == 0.0
    assert "기본 선택기" in result.reason


def test_openai_selector_uses_api_result_for_trace_analysis():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        payload = json.loads(request.read().decode("utf-8"))
        prompt = payload["input"][1]["content"][0]["text"]
        assert payload["model"] == "gpt-5-mini"
        assert payload["text"]["format"]["strict"] is True
        assert "Trace IR 요약" in prompt
        assert '"total_steps": 2' in prompt
        return httpx.Response(
            200,
            json={
                "output_text": json.dumps(
                    {
                        "selected_mode": "array-bars",
                        "reason": "배열 값이 교환되며 정렬되는 trace입니다.",
                        "confidence": 0.93,
                        "summary": "정렬 과정의 배열 상태 변화가 핵심입니다.",
                        "observations": ["arr 값이 단계적으로 바뀝니다."],
                        "learning_points": ["비교와 교환 시점을 확인하세요."],
                        "alternatives": ["array-cells", "none"],
                    },
                    ensure_ascii=False,
                )
            },
        )

    trace_result = TraceExecutionResult.from_payload(
        language="python",
        payload={
            "status": "completed",
            "stdout": "[1, 2, 3]\n",
            "stderr": "",
            "steps": [
                {
                    "line_number": 1,
                    "function_name": "<module>",
                    "locals_snapshot": {"arr": [3, 1, 2]},
                    "stdout_snapshot": "",
                },
                {
                    "line_number": 2,
                    "function_name": "<module>",
                    "locals_snapshot": {"arr": [1, 2, 3]},
                    "stdout_snapshot": "[1, 2, 3]\n",
                },
            ],
        },
    )
    client = httpx.Client(transport=httpx.MockTransport(handler))
    selector = OpenAIVisualizationSelector(
        supported_modes={"none", "array-bars", "array-cells", "call-stack"},
        fallback_selector=ManualVisualizationSelector(
            supported_modes={"none", "array-bars", "array-cells", "call-stack"},
            default_mode="none",
        ),
        api_key="test-key",
        model="gpt-5-mini",
        api_url="https://api.openai.com/v1/responses",
        timeout_seconds=5,
        http_client=client,
        default_mode="none",
    )

    result = selector.select(
        VisualizationSelectionContext(
            requested_mode="array-cells",
            source_code="arr = [3, 1, 2]\narr.sort()\nprint(arr)\n",
            language="python",
            trace_result=trace_result,
        )
    )

    assert result.selected_mode == "array-bars"
    assert result.reason == "배열 값이 교환되며 정렬되는 trace입니다."
    assert result.confidence == 0.93
    assert result.summary == "정렬 과정의 배열 상태 변화가 핵심입니다."
    assert result.observations == ["arr 값이 단계적으로 바뀝니다."]
    assert result.learning_points == ["비교와 교환 시점을 확인하세요."]
    assert result.alternatives == ["array-cells", "none"]


def test_openai_selector_falls_back_when_api_key_is_missing():
    selector = OpenAIVisualizationSelector(
        supported_modes={"none", "array-bars"},
        fallback_selector=ManualVisualizationSelector(
            supported_modes={"none", "array-bars"},
            default_mode="none",
        ),
        api_key=None,
        model="gpt-5-mini",
        api_url="https://api.openai.com/v1/responses",
        timeout_seconds=5,
        default_mode="none",
    )

    result = selector.select(
        VisualizationSelectionContext(
            requested_mode="auto",
            source_code="print('hello')\n",
            language="python",
        )
    )

    assert result.selected_mode == "none"
    assert result.confidence == 0.0
    assert "API 키" in result.reason


def test_openai_selector_falls_back_when_response_is_incomplete():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "incomplete",
                "incomplete_details": {"reason": "max_output_tokens"},
                "output": [],
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    selector = OpenAIVisualizationSelector(
        supported_modes={"none", "array-bars", "array-cells", "call-stack"},
        fallback_selector=ManualVisualizationSelector(
            supported_modes={"none", "array-bars", "array-cells", "call-stack"},
            default_mode="none",
        ),
        api_key="test-key",
        model="gpt-5-mini",
        api_url="https://api.openai.com/v1/responses",
        timeout_seconds=5,
        http_client=client,
        default_mode="none",
    )

    result = selector.select(
        VisualizationSelectionContext(
            requested_mode="array-cells",
            source_code="value = 2\nvalue = value + 5\nprint(value)\n",
            language="python",
        )
    )

    assert result.selected_mode == "array-cells"
    assert result.confidence == 1.0
    assert "실패" in result.reason


def test_openai_selector_prompt_includes_static_analysis_and_trace_ir():
    selector = OpenAIVisualizationSelector(
        supported_modes={"none", "array-bars", "stack-vertical", "dp-table"},
        fallback_selector=ManualVisualizationSelector(
            supported_modes={"none", "array-bars", "stack-vertical", "dp-table"},
            default_mode="none",
        ),
        api_key="test-key",
        model="gpt-5-mini",
        api_url="https://api.openai.com/v1/responses",
        timeout_seconds=5,
        default_mode="none",
    )

    trace_result = TraceExecutionResult.from_payload(
        language="python",
        payload={
            "status": "completed",
            "stdout": "",
            "stderr": "",
            "steps": [
                {
                    "line_number": 2,
                    "function_name": "<module>",
                    "locals_snapshot": {"dp": [[0, 0], [1, 0]]},
                    "stdout_snapshot": "",
                }
            ],
        },
    )
    prompt = selector._build_user_prompt(
        VisualizationSelectionContext(
            requested_mode="auto",
            source_code=(
                "dp = [[0, 0], [0, 0]]\n"
                "for i in range(2):\n"
                "    dp[i][0] = i\n"
                "print(dp)\n"
            ),
            language="python",
            trace_result=trace_result,
        )
    )

    assert "정적 분석 참고" in prompt
    assert "Trace IR 요약" in prompt
    assert '"dp": [[0, 0], [1, 0]]' in prompt
