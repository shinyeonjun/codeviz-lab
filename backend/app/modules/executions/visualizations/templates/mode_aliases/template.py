from collections.abc import Callable

from app.modules.executions.presentation.http.schemas import ExecutionRead, ExecutionVisualizationRead
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate


class AliasExecutionTemplate(ExecutionVisualizationTemplate):
    def __init__(
        self,
        *,
        visualization_mode: str,
        builder: Callable[[ExecutionRead], ExecutionVisualizationRead | None],
    ) -> None:
        self.visualization_mode = visualization_mode
        self._builder = builder

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        visualization = self._builder(execution)
        if visualization is None:
            return None

        metadata = dict(visualization.metadata)
        metadata["templateMode"] = self.visualization_mode
        return visualization.model_copy(update={"metadata": metadata})
