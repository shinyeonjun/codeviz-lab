import httpx

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
    assert "자동 선택기" in result.reason


def test_openai_selector_uses_api_result_for_auto_request():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        payload = request.read().decode("utf-8")
        assert '"model":"gpt-5-mini"' in payload
        assert '"strict":true' in payload
        return httpx.Response(
            200,
            json={
                "output_text": (
                    '{"selected_mode":"array-bars","reason":"숫자 배열 정렬 흐름입니다.",'
                    '"confidence":0.93,"alternatives":["array-cells","none"]}'
                )
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
            requested_mode="auto",
            source_code="numbers = [3, 1, 2]\nnumbers.sort()\nprint(numbers)\n",
            language="python",
        )
    )

    assert result.selected_mode == "array-bars"
    assert result.reason == "숫자 배열 정렬 흐름입니다."
    assert result.confidence == 0.93
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
            requested_mode="auto",
            source_code="numbers = [3, 1, 2]\nnumbers.sort()\nprint(numbers)\n",
            language="python",
        )
    )

    assert result.selected_mode == "none"
    assert result.confidence == 0.0
    assert "기본 시각화 모드" in result.reason


def test_openai_selector_prompt_includes_static_analysis_summary():
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
        )
    )

    assert "정적 분석 요약" in prompt
    assert "2차원 표 후보" in prompt
