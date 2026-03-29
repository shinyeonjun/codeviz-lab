from app.modules.executions.selection.base.interfaces import VisualizationSelectorProtocol
from app.modules.executions.selection.base.schemas import (
    VisualizationSelectionContext,
    VisualizationSelectionResult,
)


class ManualVisualizationSelector(VisualizationSelectorProtocol):
    def __init__(self, *, supported_modes: set[str], default_mode: str = "none") -> None:
        self._supported_modes = supported_modes
        self._default_mode = default_mode

    def select(self, context: VisualizationSelectionContext) -> VisualizationSelectionResult:
        if context.requested_mode == "auto":
            return VisualizationSelectionResult(
                selected_mode=self._default_mode,
                reason="자동 선택기가 비활성화되어 기본 시각화 모드를 사용합니다.",
                confidence=0.0,
                alternatives=sorted(mode for mode in self._supported_modes if mode != self._default_mode),
            )

        selected_mode = (
            context.requested_mode
            if context.requested_mode in self._supported_modes
            else self._default_mode
        )
        reason = "요청된 시각화 모드를 그대로 사용합니다."
        if selected_mode != context.requested_mode:
            reason = "지원하지 않는 시각화 모드라 기본 모드로 대체합니다."

        alternatives = sorted(mode for mode in self._supported_modes if mode != selected_mode)
        return VisualizationSelectionResult(
            selected_mode=selected_mode,
            reason=reason,
            confidence=1.0,
            alternatives=alternatives,
        )
