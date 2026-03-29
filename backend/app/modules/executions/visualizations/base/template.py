from abc import ABC, abstractmethod

from app.modules.executions.presentation.http.schemas import ExecutionRead, ExecutionVisualizationRead


class ExecutionVisualizationTemplate(ABC):
    visualization_mode: str

    @abstractmethod
    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        ...
