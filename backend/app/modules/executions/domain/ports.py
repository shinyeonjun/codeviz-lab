from typing import Protocol

from app.modules.executions.domain.trace import TraceExecutionCommand, TraceExecutionResult
from app.modules.executions.presentation.http.schemas import ExecutionRead, ExecutionVisualizationRead


class TraceRunnerProtocol(Protocol):
    def run(self, command: TraceExecutionCommand) -> TraceExecutionResult:
        ...


class ExecutionRepositoryProtocol(Protocol):
    def save_execution(
        self,
        *,
        workspace_id: str | None,
        language: str,
        visualization_mode: str,
        source_code: str,
        stdin: str,
        result: TraceExecutionResult,
    ) -> ExecutionRead:
        ...

    def get_execution(self, run_id: str) -> ExecutionRead | None:
        ...


class ExecutionVisualizerProtocol(Protocol):
    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        ...
