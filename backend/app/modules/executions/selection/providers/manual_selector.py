from app.modules.executions.selection.base.interfaces import VisualizationSelectorProtocol
from app.modules.executions.selection.base.schemas import (
    VisualizationSelectionContext,
    VisualizationSelectionResult,
)
from app.modules.executions.selection.shared import analyze_source_code, suggest_visualization_mode_from_trace


class ManualVisualizationSelector(VisualizationSelectorProtocol):
    def __init__(self, *, supported_modes: set[str], default_mode: str = "none") -> None:
        self._supported_modes = supported_modes
        self._default_mode = default_mode

    def select(self, context: VisualizationSelectionContext) -> VisualizationSelectionResult:
        if context.requested_mode == "auto":
            analysis = analyze_source_code(
                language=context.language,
                source_code=context.source_code,
                supported_modes=self._supported_modes,
            )
            selected_from_trace = self._select_from_trace(context)
            if selected_from_trace is not None:
                return VisualizationSelectionResult(
                    selected_mode=selected_from_trace,
                    reason="?ㅽ뻾 trace???곹깭 蹂?붾? 湲곗??쇰줈 ?쒓컖??紐⑤뱶瑜??좏깮?덉뒿?덈떎.",
                    confidence=0.65,
                    alternatives=sorted(mode for mode in self._supported_modes if mode != selected_from_trace),
                    summary=self._build_summary(selected_from_trace, context),
                    observations=self._build_trace_observations(context),
                )
            if analysis.suggested_mode == "hybrid":
                return VisualizationSelectionResult(
                    selected_mode="hybrid",
                    reason="자료구조 상태 변화와 제어 흐름이 함께 있어 hybrid 모드를 선택했습니다.",
                    confidence=0.78,
                    alternatives=sorted(mode for mode in self._supported_modes if mode != "hybrid"),
                    summary="flowchart와 자료구조 시각화를 같은 실행 단계로 함께 표시합니다.",
                    observations=analysis.summary_lines,
                )
            if analysis.suggested_mode == "flowchart":
                return VisualizationSelectionResult(
                    selected_mode="flowchart",
                    reason="제어문 중심 코드라 실행 흐름을 흐름도 템플릿으로 시각화합니다.",
                    confidence=0.72,
                    alternatives=sorted(mode for mode in self._supported_modes if mode != "flowchart"),
                    summary="for, while, if 같은 제어 흐름을 중심으로 flowchart 모드를 선택했습니다.",
                    observations=analysis.summary_lines,
                )

            selected_from_trace = self._select_from_trace(context)
            if selected_from_trace is not None:
                return VisualizationSelectionResult(
                    selected_mode=selected_from_trace,
                    reason="실행 trace의 상태 변화를 기준으로 시각화 모드를 선택했습니다.",
                    confidence=0.65,
                    alternatives=sorted(mode for mode in self._supported_modes if mode != selected_from_trace),
                    summary=self._build_summary(selected_from_trace, context),
                    observations=self._build_trace_observations(context),
                )

            selected_mode = analysis.suggested_mode or self._default_mode
            confidence = 0.35 if selected_mode != self._default_mode else 0.0
            reason = "정적 코드 분석 기반 기본 선택기가 시각화 모드를 결정했습니다."
            if selected_mode == self._default_mode:
                reason = "기본 선택기에서 적합한 모드를 찾지 못해 none을 선택했습니다."

            return VisualizationSelectionResult(
                selected_mode=selected_mode,
                reason=reason,
                confidence=confidence,
                alternatives=sorted(mode for mode in self._supported_modes if mode != selected_mode),
                summary=self._build_summary(selected_mode, context),
                observations=self._build_trace_observations(context),
            )

        selected_mode = (
            context.requested_mode
            if context.requested_mode in self._supported_modes
            else self._default_mode
        )
        reason = "요청된 시각화 모드를 사용합니다."
        if selected_mode != context.requested_mode:
            reason = "지원하지 않는 시각화 모드라 none으로 대체했습니다."

        alternatives = sorted(mode for mode in self._supported_modes if mode != selected_mode)
        return VisualizationSelectionResult(
            selected_mode=selected_mode,
            reason=reason,
            confidence=1.0,
            alternatives=alternatives,
            summary=self._build_summary(selected_mode, context),
            observations=self._build_trace_observations(context),
        )

    def _select_from_trace(self, context: VisualizationSelectionContext) -> str | None:
        if context.trace_result is None:
            return None
        return suggest_visualization_mode_from_trace(
            result=context.trace_result,
            supported_modes=self._supported_modes,
        )

    def _build_summary(self, selected_mode: str, context: VisualizationSelectionContext) -> str:
        if selected_mode == self._default_mode:
            return "Trace에서 뚜렷한 알고리즘 시각화 구조를 찾지 못했습니다."
        if context.requested_mode == "auto":
            return f"정적 코드 구조를 기준으로 {selected_mode} 모드를 선택했습니다."
        return f"사용자 요청에 따라 {selected_mode} 모드를 선택했습니다."

    def _build_trace_observations(self, context: VisualizationSelectionContext) -> list[str]:
        result = context.trace_result
        if result is None:
            return []

        steps = getattr(result, "steps", []) or []
        observations = [f"총 {len(steps)}개의 trace step이 생성되었습니다."]
        summary = getattr(result, "summary", None)
        function_names = getattr(summary, "function_names", []) if summary else []
        if function_names:
            observations.append(f"실행 중 관찰된 함수: {', '.join(function_names[:5])}")
        return observations
