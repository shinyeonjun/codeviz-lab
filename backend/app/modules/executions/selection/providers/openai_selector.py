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
        if context.requested_mode == "flowchart":
            return self._fallback_selector.select(context)

        if context.language not in SUPPORTED_ANALYSIS_LANGUAGES:
            return self._fallback_with_reason(context, "지원하지 않는 언어라 기본 선택기로 처리했습니다.")

        if not self._api_key:
            return self._fallback_with_reason(context, "OpenAI API 키가 없어 기본 선택기로 처리했습니다.")

        analysis = analyze_source_code(
            language=context.language,
            source_code=context.source_code,
            supported_modes=self._supported_modes,
        )
        if context.requested_mode == "auto":
            local_selection = self._fallback_selector.select(context)
            if local_selection.selected_mode not in {"none", "flowchart", "hybrid"}:
                return local_selection
        if context.requested_mode == "auto" and analysis.suggested_mode == "hybrid":
            return VisualizationSelectionResult(
                selected_mode="hybrid",
                reason="자료구조 상태 변화와 제어 흐름이 함께 있어 hybrid 모드를 선택했습니다.",
                confidence=0.78,
                alternatives=sorted(mode for mode in self._supported_modes if mode != "hybrid"),
                summary="flowchart와 자료구조 시각화를 같은 실행 단계로 함께 표시합니다.",
                observations=analysis.summary_lines,
            )
        if context.requested_mode == "auto" and analysis.suggested_mode == "flowchart":
            return VisualizationSelectionResult(
                selected_mode="flowchart",
                reason="제어문 중심 코드라 실행 흐름을 흐름도 템플릿으로 시각화합니다.",
                confidence=0.72,
                alternatives=sorted(mode for mode in self._supported_modes if mode != "flowchart"),
                summary="for, while, if 같은 제어 흐름을 중심으로 flowchart 모드를 선택했습니다.",
                observations=analysis.summary_lines,
            )

        try:
            payload = self._request_selection(context)
        except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError):
            return self._fallback_with_reason(context, "OpenAI trace 분석에 실패해 기본 선택기로 처리했습니다.")

        selected_mode = payload["selected_mode"]
        if context.requested_mode == "auto" and selected_mode == "hybrid":
            selected_mode = "flowchart" if "flowchart" in self._supported_modes else self._default_mode
        if selected_mode not in self._supported_modes:
            return self._fallback_with_reason(context, "OpenAI가 지원하지 않는 시각화 모드를 반환했습니다.")

        alternatives = [
            mode
            for mode in payload.get("alternatives", [])
            if mode in self._supported_modes and mode != selected_mode
        ]

        return VisualizationSelectionResult(
            selected_mode=selected_mode,
            reason=str(payload.get("reason") or "Trace IR을 분석해 시각화 모드를 선택했습니다."),
            confidence=self._normalize_confidence(payload.get("confidence")),
            alternatives=alternatives,
            summary=str(payload.get("summary") or ""),
            observations=self._string_list(payload.get("observations"), limit=5),
            learning_points=self._string_list(payload.get("learning_points"), limit=5),
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
                    "name": "visualization_trace_analysis",
                    "strict": True,
                    "schema": self._build_response_schema(),
                },
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
            "너는 CodeViz의 알고리즘 학습용 trace 분석기다.\n"
            "입력으로 사용자 코드, 실행 후 Trace IR, 지원되는 시각화 모드 목록을 받는다.\n"
            "코드 이름이나 주석만 믿지 말고, Trace IR의 상태 변화, call stack, stdout, 자료구조 변화를 우선한다.\n"
            "요청 모드는 사용자의 힌트일 뿐이며, trace가 더 적합한 모드를 보여주면 다른 모드를 선택해도 된다.\n"
            "학습자가 이해할 수 있도록 한국어로 짧고 구체적으로 분석한다.\n"
            "지원 목록에 없는 모드는 절대 선택하지 않는다. trace에 변수/자료구조 변화가 있으면 가능한 한 시각화 모드를 선택한다.\n"
            "none은 trace step이 없거나 출력만 있고 추적할 상태 변화가 전혀 없을 때만 선택한다.\n"
            "Python, C, Java 모두 같은 시각화 모드 체계를 사용한다.\n\n"
            "주요 모드 기준:\n"
            "- array-bars: 숫자 배열의 정렬, swap, shift, 비교, 인덱스 이동이 핵심일 때\n"
            "- array-cells: 배열/리스트/문자열의 값 조회, 수정, 탐색 상태 또는 단일 스칼라 변수 값 변화가 핵심일 때\n"
            "- stack-vertical: LIFO push/pop 흐름이 핵심일 때\n"
            "- queue-horizontal: FIFO enqueue/dequeue 흐름이 핵심일 때\n"
            "- call-stack: 함수 호출, 재귀, 프레임 변화가 핵심일 때\n"
            "- dp-table: 2차원 표나 점화식 상태가 단계적으로 채워질 때\n"
            "- tree-binary: left/right 자식 기반 트리 구조가 핵심일 때\n"
            "- graph-node-edge: 인접 리스트, visited, BFS/DFS 같은 그래프 순회가 핵심일 때\n"
            "- flowchart: for, while, if/else처럼 제어 흐름 자체를 배우는 단순 코드일 때\n"
            "- hybrid: 배열/스택/큐/그래프 같은 자료구조 상태 변화와 for/while/if 제어 흐름이 모두 중요할 때\n"
            "- none: 단순 출력, 단일 계산, trace로 볼 구조가 부족할 때"
        )

    def _build_user_prompt(self, context: VisualizationSelectionContext) -> str:
        source_code = context.source_code
        if len(source_code) > 6000:
            source_code = f"{source_code[:6000]}\n... 이하 코드는 길이 제한으로 생략됨"

        static_summary = self._build_static_summary(context)
        trace_summary = self._build_trace_prompt_payload(context)
        fence_language = context.language if context.language in {"python", "c", "java"} else "text"

        return (
            f"언어: {context.language}\n"
            f"요청 모드 힌트: {context.requested_mode}\n"
            f"지원 시각화 모드: {', '.join(sorted(self._supported_modes))}\n\n"
            "실행 후 Trace IR을 가장 중요한 근거로 삼아 템플릿을 선택하고, 패널에 보여줄 분석을 작성해줘.\n"
            "출력은 지정된 JSON schema만 따른다.\n\n"
            "정적 분석 참고:\n"
            f"{static_summary}\n\n"
            "Trace IR 요약:\n"
            f"{trace_summary}\n\n"
            "사용자 코드:\n"
            f"```{fence_language}\n"
            f"{source_code}\n"
            "```"
        )

    def _build_static_summary(self, context: VisualizationSelectionContext) -> str:
        analysis_snapshot = analyze_source_code(
            language=context.language,
            source_code=context.source_code,
            supported_modes=self._supported_modes,
        )
        if not analysis_snapshot.summary_lines:
            return "- 정적 분석에서 뚜렷한 알고리즘 구조를 찾지 못했습니다."
        return "\n".join(f"- {line}" for line in analysis_snapshot.summary_lines)

    def _build_trace_prompt_payload(self, context: VisualizationSelectionContext) -> str:
        result = context.trace_result
        if result is None:
            return json.dumps({"available": False}, ensure_ascii=False)

        steps = list(getattr(result, "steps", []) or [])
        sampled_steps = self._sample_trace_steps(steps)
        payload = {
            "available": True,
            "status": getattr(result, "status", ""),
            "stdout": self._short_text(getattr(result, "stdout", "")),
            "stderr": self._short_text(getattr(result, "stderr", "")),
            "error_message": self._short_text(getattr(result, "error_message", "") or ""),
            "total_steps": len(steps),
            "summary": self._trace_summary_dict(result),
            "sampled_steps": [self._step_to_prompt_dict(index, step) for index, step in sampled_steps],
        }
        return json.dumps(payload, ensure_ascii=False, default=str)

    def _trace_summary_dict(self, result: Any) -> dict[str, Any]:
        summary = getattr(result, "summary", None)
        if summary is None:
            return {}
        return {
            "total_steps": getattr(summary, "total_steps", 0),
            "function_names": getattr(summary, "function_names", []),
            "has_stdout": getattr(summary, "has_stdout", False),
            "has_errors": getattr(summary, "has_errors", False),
        }

    def _sample_trace_steps(self, steps: list[Any]) -> list[tuple[int, Any]]:
        if len(steps) <= 24:
            return list(enumerate(steps, start=1))

        indexed = list(enumerate(steps, start=1))
        selected = indexed[:12] + indexed[-8:]
        midpoint = indexed[len(indexed) // 2]
        if midpoint not in selected:
            selected.insert(12, midpoint)
        return selected

    def _step_to_prompt_dict(self, index: int, step: Any) -> dict[str, Any]:
        return {
            "step_index": index,
            "line_number": getattr(step, "line_number", 0),
            "event_type": getattr(step, "event_type", ""),
            "function_name": getattr(step, "function_name", ""),
            "locals": self._compact_mapping(getattr(step, "locals_snapshot", {})),
            "globals": self._compact_mapping(getattr(step, "globals_snapshot", {})),
            "stdout": self._short_text(getattr(step, "stdout_snapshot", "")),
            "call_stack": [
                {
                    "function_name": getattr(frame, "function_name", ""),
                    "line_number": getattr(frame, "line_number", None),
                }
                for frame in (getattr(step, "call_stack", []) or [])
            ][-8:],
            "metadata": self._compact_mapping(getattr(step, "metadata", {})),
        }

    def _compact_mapping(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        compacted: dict[str, Any] = {}
        for key, item in list(value.items())[:12]:
            compacted[str(key)] = self._compact_value(item)
        return compacted

    def _compact_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): self._compact_value(item) for key, item in list(value.items())[:8]}
        if isinstance(value, list):
            preview = [self._compact_value(item) for item in value[:12]]
            if len(value) > 12:
                preview.append(f"... {len(value) - 12} more")
            return preview
        if isinstance(value, tuple):
            return self._compact_value(list(value))
        if isinstance(value, str):
            return self._short_text(value, limit=160)
        return value

    def _short_text(self, value: Any, *, limit: int = 500) -> str:
        text = value if isinstance(value, str) else str(value)
        if len(text) <= limit:
            return text
        return f"{text[:limit]}... 생략"

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
                "summary": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 500,
                },
                "observations": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 180,
                    },
                    "maxItems": 5,
                },
                "learning_points": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 180,
                    },
                    "maxItems": 5,
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
            "required": [
                "selected_mode",
                "reason",
                "confidence",
                "summary",
                "observations",
                "learning_points",
                "alternatives",
            ],
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

    def _fallback_with_reason(
        self,
        context: VisualizationSelectionContext,
        reason: str,
    ) -> VisualizationSelectionResult:
        fallback = self._fallback_selector.select(context)
        if context.requested_mode == "auto" and fallback.selected_mode not in self._supported_modes:
            fallback = VisualizationSelectionResult(selected_mode=self._default_mode)
        return VisualizationSelectionResult(
            selected_mode=fallback.selected_mode,
            reason=reason,
            confidence=fallback.confidence,
            alternatives=fallback.alternatives,
            summary=fallback.summary,
            observations=fallback.observations,
            learning_points=fallback.learning_points,
        )

    def _normalize_confidence(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            normalized = float(value)
        except (TypeError, ValueError):
            return None
        return max(0.0, min(1.0, normalized))

    def _string_list(self, value: Any, *, limit: int) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value[:limit] if str(item).strip()]
