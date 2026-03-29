from app.modules.auth.domain.context import AuthContext
from app.modules.auth.presentation.http.schemas import (
    ExamAttemptActivityRead,
    ExecutionActivityRead,
    WorkspaceActivityRead,
    WorkspaceRead,
)
from app.modules.exams.infrastructure.persistence.repository import ExamAttemptRepository
from app.modules.executions.infrastructure.persistence.repository import SqlAlchemyExecutionRepository


class WorkspaceActivityService:
    def __init__(
        self,
        *,
        execution_repository: SqlAlchemyExecutionRepository,
        exam_attempt_repository: ExamAttemptRepository,
    ) -> None:
        self._execution_repository = execution_repository
        self._exam_attempt_repository = exam_attempt_repository

    def read_activity(self, *, context: AuthContext) -> WorkspaceActivityRead:
        executions = self._execution_repository.list_recent_executions(workspace_id=context.workspace.id, limit=5)
        attempts = self._exam_attempt_repository.list_recent_attempts(workspace_id=context.workspace.id, limit=5)

        return WorkspaceActivityRead(
            current_workspace=WorkspaceRead(
                id=context.workspace.id,
                title=context.workspace.title,
                is_guest=context.workspace.is_guest,
                created_at=context.workspace.created_at,
            ),
            recent_executions=[
                ExecutionActivityRead(
                    run_id=run.id,
                    status=run.status,
                    visualization_mode=run.visualization_mode,
                    source_preview=(run.source_code[:80] + "…") if len(run.source_code) > 80 else run.source_code,
                    created_at=run.created_at,
                )
                for run in executions
            ],
            recent_exam_attempts=[
                ExamAttemptActivityRead(
                    attempt_id=attempt.id,
                    lesson_id=attempt.lesson_id,
                    question_id=attempt.question_id,
                    status=attempt.status,
                    score=attempt.score,
                    created_at=attempt.created_at,
                )
                for attempt in attempts
            ],
        )
