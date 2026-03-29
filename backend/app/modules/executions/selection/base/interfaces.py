from typing import Protocol

from app.modules.executions.selection.base.schemas import (
    VisualizationSelectionContext,
    VisualizationSelectionResult,
)


class VisualizationSelectorProtocol(Protocol):
    def select(self, context: VisualizationSelectionContext) -> VisualizationSelectionResult:
        ...
