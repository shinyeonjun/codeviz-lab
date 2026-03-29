from app.modules.executions.presentation.http.schemas import ExecutionRead, ExecutionVisualizationRead
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate


class NoVisualizationExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "none"

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        return None
