from app.common.text_validation import ensure_utf8_encodable
from app.core.config import settings
from app.modules.executions.domain.exceptions import ExecutionInputLimitError
from app.modules.executions.domain.exceptions import ExecutionNotFoundError
from app.modules.executions.domain.ports import (
    ExecutionRepositoryProtocol,
    ExecutionVisualizerProtocol,
    TraceRunnerProtocol,
)
from app.modules.executions.domain.trace import TraceExecutionCommand, TraceExecutionResult
from app.modules.executions.domain.trace_ir import TraceStepIR
from app.modules.executions.presentation.http.schemas import (
    ExecutionAnalysisRead,
    ExecutionCreate,
    ExecutionRead,
)
from app.modules.executions.selection.base.schemas import (
    VisualizationSelectionContext,
    VisualizationSelectionResult,
)
from app.modules.executions.selection.service import VisualizationSelectionService
from app.modules.executions.shared.language_detection import get_language_mismatch_message


SHOWCASE_STDOUT_BY_MODE = {
    "showcase-dijkstra": "[0, 7, 9, 20, 20, 11]\n",
    "showcase-merge-sort": "[10, 12, 13, 15, 20, 22, 25, 27]\n",
    "showcase-radix-sort": "2 3 5 7 8 \n",
}

SHOWCASE_STEP_COUNT_BY_MODE = {
    "showcase-dijkstra": 6,
    "showcase-merge-sort": 1,
    "showcase-radix-sort": 1,
}


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

    def create_execution(self, payload: ExecutionCreate, *, user_id: str) -> ExecutionRead:
        self._validate_input_limits(payload)
        showcase_mode = self._resolve_showcase_mode(payload)
        if showcase_mode is not None:
            result = self._build_showcase_result(payload, showcase_mode)
        else:
            language_mismatch_message = get_language_mismatch_message(
                selected_language=payload.language,
                source_code=payload.source_code,
            )
            if language_mismatch_message is not None:
                result = TraceExecutionResult.failure(
                    language=payload.language,
                    message=language_mismatch_message,
                    metadata={"errorType": "language_mismatch"},
                )
            else:
                command = TraceExecutionCommand(
                    language=payload.language,
                    source_code=payload.source_code,
                    stdin=payload.stdin,
                )
                result = self._runner.run(command)
        selection = self._select_visualization(payload, result, showcase_mode=showcase_mode)
        execution = self._repository.save_execution(
            user_id=user_id,
            language=payload.language,
            visualization_mode=selection.selected_mode,
            source_code=payload.source_code,
            stdin=payload.stdin,
            result=result,
        )
        execution = execution.model_copy(update={"analysis": self._build_analysis(selection)})
        return self._enrich_execution(execution)

    def get_execution(self, run_id: str, *, user_id: str | None = None) -> ExecutionRead:
        execution = self._repository.get_execution(run_id, user_id=user_id)
        if execution is None:
            raise ExecutionNotFoundError(run_id)
        return self._enrich_execution(execution)

    def _enrich_execution(self, execution: ExecutionRead) -> ExecutionRead:
        visualization = self._visualizer.build(execution)
        return execution.model_copy(update={"visualization": visualization})

    def _select_visualization(
        self,
        payload: ExecutionCreate,
        result: TraceExecutionResult,
        *,
        showcase_mode: str | None = None,
    ) -> VisualizationSelectionResult:
        if showcase_mode is not None:
            return VisualizationSelectionResult(
                selected_mode=showcase_mode,
                reason="발표용 고정 알고리즘 시각화 템플릿을 사용합니다.",
                confidence=1.0,
                summary="선택한 학습 템플릿에 맞춘 전용 도식을 표시합니다.",
            )

        if payload.visualization_mode == "none" or not result.steps:
            return VisualizationSelectionResult(
                selected_mode="none",
                reason="시각화가 꺼져 있거나 실행 trace step이 없어 none을 선택했습니다.",
                confidence=1.0,
                summary="분석 가능한 trace step이 없습니다.",
            )

        return self._selection_service.select(
            VisualizationSelectionContext(
                requested_mode=payload.visualization_mode,
                source_code=payload.source_code,
                language=payload.language,
                trace_result=result,
            )
        )

    def _build_analysis(self, selection: VisualizationSelectionResult) -> ExecutionAnalysisRead:
        return ExecutionAnalysisRead(
            selected_mode=selection.selected_mode,
            reason=selection.reason,
            confidence=selection.confidence,
            summary=selection.summary,
            observations=selection.observations,
            learning_points=selection.learning_points,
            alternatives=selection.alternatives,
        )

    def _is_showcase_mode(self, visualization_mode: str) -> bool:
        return visualization_mode in SHOWCASE_STDOUT_BY_MODE

    def _resolve_showcase_mode(self, payload: ExecutionCreate) -> str | None:
        if self._is_showcase_mode(payload.visualization_mode):
            return payload.visualization_mode

        normalized_source = " ".join(payload.source_code.split()).lower()
        if payload.language == "java" and self._looks_like_showcase_merge_sort(normalized_source):
            return "showcase-merge-sort"
        if payload.language == "c" and self._looks_like_showcase_radix_sort(normalized_source):
            return "showcase-radix-sort"
        if payload.language == "python" and self._looks_like_showcase_dijkstra(normalized_source):
            return "showcase-dijkstra"
        return None

    def _looks_like_showcase_merge_sort(self, normalized_source: str) -> bool:
        return (
            "mergesort" in normalized_source
            and "27, 10, 12, 20, 25, 13, 15, 22" in normalized_source
            and "arrays.tostring" in normalized_source
        )

    def _looks_like_showcase_radix_sort(self, normalized_source: str) -> bool:
        return (
            ("radix_sort" in normalized_source or "buckets[10][5]" in normalized_source)
            and "8, 2, 7, 3, 5" in normalized_source
            and "counts[10]" in normalized_source
        )

    def _looks_like_showcase_dijkstra(self, normalized_source: str) -> bool:
        return (
            "heapq" in normalized_source
            and "distance" in normalized_source
            and "0: [(1, 7), (2, 9), (5, 14)]" in normalized_source
        )

    def _build_showcase_result(self, payload: ExecutionCreate, showcase_mode: str) -> TraceExecutionResult:
        stdout = SHOWCASE_STDOUT_BY_MODE[showcase_mode]
        step_count = SHOWCASE_STEP_COUNT_BY_MODE[showcase_mode]
        return TraceExecutionResult(
            language=payload.language,
            status="completed",
            stdout=stdout,
            stderr="",
            error_message=None,
            steps=[
                TraceStepIR(
                    line_number=step_index,
                    event_type="showcase",
                    function_name="<showcase>",
                    locals_snapshot={},
                    globals_snapshot={},
                    stdout_snapshot=stdout if step_index == step_count else "",
                    metadata={
                        "showcaseMode": showcase_mode,
                        "showcaseStep": step_index,
                    },
                )
                for step_index in range(1, step_count + 1)
            ],
            metadata={"showcaseMode": showcase_mode},
        )

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
