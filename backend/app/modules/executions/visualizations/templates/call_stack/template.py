from app.modules.executions.presentation.http.schemas import ExecutionRead, ExecutionVisualizationRead
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate
from app.modules.executions.visualizations.shared.call_stack import (
    build_call_stack_visualization,
)


class CallStackExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "call-stack"

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        return build_call_stack_visualization(execution)
