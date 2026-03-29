from __future__ import annotations

import json
from typing import Any

import httpx

from app.modules.executions.selection.base.interfaces import VisualizationSelectorProtocol
from app.modules.executions.selection.base.schemas import (
    VisualizationSelectionContext,
    VisualizationSelectionResult,
)
from app.modules.executions.selection.shared import (
    SUPPORTED_ANALYSIS_LANGUAGES,
    analyze_source_code,
)


class OpenAIVisualizationSelector(VisualizationSelectorProtocol):
    def __init__(
        self,
        *,
        supported_modes: set[str],
        fallback_selector: VisualizationSelectorProtocol,
        api_key: str | None,
        model: str,
        api_url: str,
        timeout_seconds: int,
        max_output_tokens: int = 600,
        reasoning_effort: str = "low",
        text_verbosity: str = "low",
        project_id: str | None = None,
        organization_id: str | None = None,
        http_client: httpx.Client | None = None,
        default_mode: str = "none",
    ) -> None:
        self._supported_modes = supported_modes
        self._fallback_selector = fallback_selector
        self._api_key = api_key
        self._model = model
        self._api_url = api_url
        self._timeout_seconds = timeout_seconds
        self._max_output_tokens = max_output_tokens
        self._reasoning_effort = reasoning_effort
        self._text_verbosity = text_verbosity
        self._project_id = project_id
        self._organization_id = organization_id
        self._http_client = http_client
        self._default_mode = default_mode

    def select(self, context: VisualizationSelectionContext) -> VisualizationSelectionResult:
        if context.requested_mode != "auto":
            return self._fallback_selector.select(context)

        if context.language not in SUPPORTED_ANALYSIS_LANGUAGES:
            return self._build_auto_fallback_result(
                "현재 자동 시각화 선택이 지원되지 않는 언어라 기본 시각화 모드를 사용합니다."
            )

        if not self._api_key:
            return self._build_auto_fallback_result("OpenAI API 키가 없어 기본 시각화 모드를 사용합니다.")

        try:
            payload = self._request_selection(context)
        except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError):
            return self._build_auto_fallback_result(
                "OpenAI 시각화 선택에 실패해 기본 시각화 모드를 사용합니다."
            )

        selected_mode = payload["selected_mode"]
        if selected_mode not in self._supported_modes:
            return self._build_auto_fallback_result(
                "OpenAI가 지원하지 않는 시각화 모드를 반환해 기본 시각화 모드를 사용합니다."
            )

        alternatives = [
            mode
            for mode in payload.get("alternatives", [])
            if mode in self._supported_modes and mode != selected_mode
        ]

        return VisualizationSelectionResult(
            selected_mode=selected_mode,
            reason=payload.get("reason", "OpenAI가 코드를 분석해 시각화 모드를 선택했습니다."),
            confidence=self._normalize_confidence(payload.get("confidence")),
            alternatives=alternatives,
        )

    def _request_selection(self, context: VisualizationSelectionContext) -> dict[str, Any]:
        request_payload = {
            "model": self._model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": self._build_system_prompt(),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": self._build_user_prompt(context),
                        }
                    ],
                },
            ],
            "max_output_tokens": self._max_output_tokens,
            "reasoning": {
                "effort": self._reasoning_effort,
            },
            "text": {
                "verbosity": self._text_verbosity,
                "format": {
                    "type": "json_schema",
                    "name": "visualization_selection",
                    "strict": True,
                    "schema": self._build_response_schema(),
                }
            },
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if self._project_id:
            headers["OpenAI-Project"] = self._project_id
        if self._organization_id:
            headers["OpenAI-Organization"] = self._organization_id

        client = self._http_client or httpx.Client(timeout=self._timeout_seconds)
        should_close = self._http_client is None

        try:
            response = client.post(self._api_url, json=request_payload, headers=headers)
            response.raise_for_status()
        finally:
            if should_close:
                client.close()

        payload = response.json()
        output_text = self._extract_output_text(payload)
        return json.loads(output_text)

    def _build_system_prompt(self) -> str:
        return (
            "너는 코드 학습 플랫폼의 시각화 템플릿 선택기다.\n"
            "반드시 지원된 시각화 모드 중 하나만 선택한다.\n"
            "코드를 실행하기 전에 정적 코드 구조만 보고 판단한다.\n"
            "가장 중요한 기준은 학습 효과다.\n"
            "변수명만 보고 추정하지 말고, 실제 문법 구조와 자료 구조 패턴을 우선한다.\n"
            "명백한 구조가 없거나 여러 구조가 섞여 교육적으로 애매하면 none을 선택한다.\n"
            "대안은 3개 이하로, 실제 후보만 우선순위 순서로 제시한다.\n"
            "reason은 한 문장 한국어로 짧고 구체적으로 쓴다.\n"
            "confidence는 0~1 사이 실수로, 구조가 명확할수록 높인다.\n"
            "Python과 C 모두 같은 템플릿 체계를 사용한다.\n"
            "판단 기준:\n"
            "- array-bars: 숫자 배열의 정렬, 교환, shift, 삽입, 비교 인덱스 이동이 핵심일 때\n"
            "- array-selection-sort / array-bubble-sort / array-merge-process / array-quick-partition / array-heapify / array-shell-sort: 정렬 단계가 더 구체적으로 드러날 때\n"
            "- array-cells: 일반 리스트, 문자열 토큰, 배열 셀 값 수정/탐색이 핵심일 때\n"
            "- binary-search-window / lower-bound-search / upper-bound-search: 정렬된 배열에서 low, high, mid 범위가 줄어드는 탐색이 핵심일 때\n"
            "- two-pointers-opposite / two-pointers-same-direction: 두 개의 포인터가 배열 위를 이동하며 조건을 맞출 때\n"
            "- sliding-window-fixed / sliding-window-variable: 연속 구간이 확장/축소되며 상태가 변할 때\n"
            "- prefix-sum-array / palindrome-pointers: 누적 배열이나 문자열/배열 양끝 비교가 핵심일 때\n"
            "- stack-vertical: append/pop 또는 LIFO 패턴이 핵심일 때\n"
            "- monotonic-stack / stack-expression: 스택이 계산 흐름이나 단조성 유지에 쓰일 때\n"
            "- queue-horizontal: append + pop(0), popleft, dequeue 등 FIFO 패턴이 핵심일 때\n"
            "- deque-both-ends: 양쪽 끝에서 삽입/삭제가 모두 일어날 때\n"
            "- call-stack: 함수 호출 체인, 재귀, 프레임 흐름이 핵심일 때\n"
            "- recursion-tree / backtracking-tree / divide-and-conquer / memoized-recursion: 재귀 호출 분기나 되돌아감이 핵심일 때\n"
            "- dp-table: 2차원 리스트/표를 채우는 상태 전이가 핵심일 때\n"
            "- knapsack-table / lcs-table / edit-distance-table / grid-dp: DP 테이블의 의미가 더 구체적으로 보일 때\n"
            "- tree-binary: left/right 자식 구조나 value-left-right 노드 구조가 핵심일 때\n"
            "- tree-level-order / tree-bst-search / tree-bst-insert: 트리 순회나 BST 탐색/삽입 흐름이 핵심일 때\n"
            "- graph-node-edge: 인접 리스트, 노드-간선 연결, visited 기반 순회가 핵심일 때\n"
            "- graph-bfs-traversal / graph-dfs-traversal / graph-topological-sort / graph-connected-components / graph-cycle-detection / graph-bipartite-check: 그래프 순회/분할/판별 흐름이 핵심일 때\n"
            "- none: 단순 입출력, 스칼라 계산, 템플릿 적합도가 낮은 경우"
        )

    def _build_user_prompt(self, context: VisualizationSelectionContext) -> str:
        source_code = context.source_code
        if len(source_code) > 6000:
            source_code = f"{source_code[:6000]}\n... 이하 코드는 길이 제한으로 생략됨"

        analysis_snapshot = analyze_source_code(
            language=context.language,
            source_code=context.source_code,
            supported_modes=self._supported_modes,
        )
        analysis_summary = "\n".join(
            f"- {line}" for line in analysis_snapshot.summary_lines
        )
        fence_language = "python" if context.language == "python" else "c"

        return (
            f"언어: {context.language}\n"
            f"지원 시각화 모드: {', '.join(sorted(self._supported_modes))}\n"
            "아래 코드를 학습 시각화하기에 가장 적절한 템플릿을 고르세요.\n"
            "먼저 정적 분석 요약을 참고하고, 그다음 원본 코드를 확인하세요.\n"
            "출력은 JSON schema만 따르세요.\n\n"
            "정적 분석 요약:\n"
            f"{analysis_summary}\n\n"
            f"```{fence_language}\n"
            f"{source_code}\n"
            "```"
        )

    def _build_response_schema(self) -> dict[str, Any]:
        mode_enum = sorted(self._supported_modes)
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "selected_mode": {
                    "type": "string",
                    "enum": mode_enum,
                },
                "reason": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 300,
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
                "alternatives": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": mode_enum,
                    },
                    "maxItems": 3,
                },
            },
            "required": ["selected_mode", "reason", "confidence", "alternatives"],
        }

    def _extract_output_text(self, payload: dict[str, Any]) -> str:
        if payload.get("status") == "incomplete":
            reason = payload.get("incomplete_details", {}).get("reason", "unknown")
            raise ValueError(f"OpenAI 응답이 완료되지 않았습니다: {reason}")

        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        for item in payload.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    return text

        raise ValueError("OpenAI 응답에서 구조화된 텍스트를 찾지 못했습니다.")

    def _build_auto_fallback_result(self, reason: str) -> VisualizationSelectionResult:
        return VisualizationSelectionResult(
            selected_mode=self._default_mode,
            reason=reason,
            confidence=0.0,
            alternatives=sorted(mode for mode in self._supported_modes if mode != self._default_mode),
        )

    def _normalize_confidence(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            normalized = float(value)
        except (TypeError, ValueError):
            return None
        return max(0.0, min(1.0, normalized))
