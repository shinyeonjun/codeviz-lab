from app.modules.executions.presentation.http.schemas import ExecutionRead, ExecutionVisualizationRead
from app.modules.executions.visualizations.base.registry import ExecutionVisualizationRegistry


class ExecutionVisualizationService:
    def __init__(self, *, registry: ExecutionVisualizationRegistry) -> None:
        self._registry = registry

    @property
    def supported_modes(self) -> set[str]:
        return self._registry.supported_modes

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        template = self._registry.get(execution.visualization_mode)
        if template is None:
            return None
        return template.build(execution)
