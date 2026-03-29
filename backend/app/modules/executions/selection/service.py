from app.modules.executions.selection.base.interfaces import VisualizationSelectorProtocol
from app.modules.executions.selection.base.schemas import (
    VisualizationSelectionContext,
    VisualizationSelectionResult,
)


class VisualizationSelectionService:
    def __init__(self, *, selector: VisualizationSelectorProtocol) -> None:
        self._selector = selector

    def select(self, context: VisualizationSelectionContext) -> VisualizationSelectionResult:
        return self._selector.select(context)
