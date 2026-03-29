from app.modules.executions.selection.base.interfaces import VisualizationSelectorProtocol
from app.modules.executions.selection.base.schemas import (
    VisualizationSelectionContext,
    VisualizationSelectionResult,
)


class LocalVisualizationSelector(VisualizationSelectorProtocol):
    def select(self, context: VisualizationSelectionContext) -> VisualizationSelectionResult:
        raise NotImplementedError("로컬 모델 기반 시각화 선택기는 아직 연결되지 않았습니다.")
