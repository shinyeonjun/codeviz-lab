from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.executions.domain.trace import TraceExecutionResult
from app.modules.executions.infrastructure.persistence.models import ExecutionRun, ExecutionStep
from app.modules.executions.presentation.http.schemas import ExecutionRead, ExecutionStepRead


class SqlAlchemyExecutionRepository:
    def __init__(self, *, session: Session) -> None:
        self._session = session

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
        run = ExecutionRun(
            id=str(uuid4()),
            workspace_id=workspace_id,
            language=language,
            visualization_mode=visualization_mode,
            status=result.status,
            source_code=source_code,
            stdin=stdin,
            stdout=result.stdout,
            stderr=result.stderr,
            error_message=result.error_message,
            step_count=len(result.steps),
            completed_at=datetime.now(UTC),
        )
        self._session.add(run)
        self._session.flush()

        for index, step in enumerate(result.steps, start=1):
            self._session.add(
                ExecutionStep(
                    run_id=run.id,
                    step_index=index,
                    line_number=step.line_number,
                    event_type=step.event_type,
                    function_name=step.function_name,
                    locals_snapshot=step.locals_snapshot,
                    stdout_snapshot=step.stdout_snapshot,
                    error_message=step.error_message,
                )
            )

        self._session.commit()
        return self.get_execution(run.id)  # type: ignore[return-value]

    def get_execution(self, run_id: str) -> ExecutionRead | None:
        statement = (
            select(ExecutionRun)
            .options(selectinload(ExecutionRun.steps))
            .where(ExecutionRun.id == run_id)
        )
        run = self._session.execute(statement).scalar_one_or_none()
        if run is None:
            return None
        return self._to_schema(run)

    def list_recent_executions(self, *, workspace_id: str, limit: int = 5) -> list[ExecutionRun]:
        statement = (
            select(ExecutionRun)
            .where(ExecutionRun.workspace_id == workspace_id)
            .order_by(ExecutionRun.created_at.desc())
            .limit(limit)
        )
        return list(self._session.execute(statement).scalars().all())

    def _to_schema(self, run: ExecutionRun) -> ExecutionRead:
        steps = [
            ExecutionStepRead(
                step_index=step.step_index,
                line_number=step.line_number,
                event_type=step.event_type,
                function_name=step.function_name,
                locals_snapshot=step.locals_snapshot,
                stdout_snapshot=step.stdout_snapshot,
                error_message=step.error_message,
            )
            for step in sorted(run.steps, key=lambda item: item.step_index)
        ]

        return ExecutionRead(
            run_id=run.id,
            language=run.language,
            visualization_mode=run.visualization_mode,
            status=run.status,
            source_code=run.source_code,
            stdin=run.stdin,
            stdout=run.stdout,
            stderr=run.stderr,
            error_message=run.error_message,
            step_count=run.step_count,
            created_at=run.created_at,
            completed_at=run.completed_at,
            steps=steps,
        )
