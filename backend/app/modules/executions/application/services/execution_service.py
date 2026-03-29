from app.common.text_validation import ensure_utf8_encodable
from app.core.config import settings
from app.modules.executions.domain.exceptions import ExecutionInputLimitError
from app.modules.executions.domain.exceptions import ExecutionNotFoundError
from app.modules.executions.domain.ports import (
    ExecutionRepositoryProtocol,
    ExecutionVisualizerProtocol,
    TraceRunnerProtocol,
)
from app.modules.executions.domain.trace import TraceExecutionCommand
from app.modules.executions.presentation.http.schemas import ExecutionCreate, ExecutionRead
from app.modules.executions.selection.base.schemas import VisualizationSelectionContext
from app.modules.executions.selection.service import VisualizationSelectionService


class ExecutionService:
    def __init__(
        self,
        *,
        repository: ExecutionRepositoryProtocol,
        runner: TraceRunnerProtocol,
        visualizer: ExecutionVisualizerProtocol,
        selection_service: VisualizationSelectionService,
    ) -> None:
        self._repository = repository
        self._runner = runner
        self._visualizer = visualizer
        self._selection_service = selection_service

    def create_execution(self, payload: ExecutionCreate, *, workspace_id: str | None = None) -> ExecutionRead:
        self._validate_input_limits(payload)
        selection = self._selection_service.select(
            VisualizationSelectionContext(
                requested_mode=payload.visualization_mode,
                source_code=payload.source_code,
                language=payload.language,
            )
        )
        command = TraceExecutionCommand(
            language=payload.language,
            source_code=payload.source_code,
            stdin=payload.stdin,
        )
        result = self._runner.run(command)
        execution = self._repository.save_execution(
            workspace_id=workspace_id,
            language=payload.language,
            visualization_mode=selection.selected_mode,
            source_code=payload.source_code,
            stdin=payload.stdin,
            result=result,
        )
        return self._enrich_execution(execution)

    def get_execution(self, run_id: str) -> ExecutionRead:
        execution = self._repository.get_execution(run_id)
        if execution is None:
            raise ExecutionNotFoundError(run_id)
        return self._enrich_execution(execution)

    def _enrich_execution(self, execution: ExecutionRead) -> ExecutionRead:
        visualization = self._visualizer.build(execution)
        return execution.model_copy(update={"visualization": visualization})

    def _validate_input_limits(self, payload: ExecutionCreate) -> None:
        if len(payload.source_code) > settings.runner_max_source_code_chars:
            raise ExecutionInputLimitError("소스 코드 길이가 허용 범위를 초과했습니다.")
        if len(payload.stdin) > settings.runner_max_stdin_chars:
            raise ExecutionInputLimitError("표준 입력 길이가 허용 범위를 초과했습니다.")
        try:
            ensure_utf8_encodable(payload.source_code, field_label="소스 코드")
            ensure_utf8_encodable(payload.stdin, field_label="표준 입력")
        except ValueError as error:
            raise ExecutionInputLimitError(str(error)) from error
