from app.modules.executions.presentation.http.schemas import ExecutionRead, ExecutionVisualizationRead
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate
from app.modules.executions.visualizations.shared.array_sequences import (
    build_array_visualization,
)


class ArrayBarsExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "array-bars"

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        return build_array_visualization(execution)
