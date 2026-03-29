from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.modules.executions.application.dependencies import get_trace_runner
from app.modules.executions.domain.exceptions import ExecutionInputLimitError
from app.modules.executions.domain.ports import TraceRunnerProtocol
from app.modules.auth.application.dependencies import get_optional_auth_context
from app.modules.auth.domain.context import AuthContext
from app.modules.exams.application.services.exam_grading_service import ExamGradingService
from app.common.responses import success_response
from app.core.database import get_db_session
from app.modules.exams.application.services.exam_service import (
    ExamService,
    get_exam_service,
)
from app.modules.exams.domain.exceptions import (
    ExamAssessmentNotConfiguredError,
    ExamCategoryNotFoundError,
    ExamLessonNotFoundError,
)
from app.modules.exams.infrastructure.persistence.repository import ExamAttemptRepository
from app.modules.exams.presentation.http.schemas import (
    ExamCategoryRead,
    ExamSubmissionCreate,
    ExamSubmissionRead,
    ExamSessionCreate,
    ExamSessionRead,
)

router = APIRouter()


def get_exam_grading_service(
    service: ExamService = Depends(get_exam_service),
    runner: TraceRunnerProtocol = Depends(get_trace_runner),
) -> ExamGradingService:
    return ExamGradingService(exam_service=service, runner=runner)


def get_exam_attempt_repository(
    session: Session = Depends(get_db_session),
) -> ExamAttemptRepository:
    return ExamAttemptRepository(session=session)


@router.get("/categories")
def read_exam_categories(
    service: ExamService = Depends(get_exam_service),
) -> dict[str, object]:
    categories: list[ExamCategoryRead] = service.get_categories()
    return success_response(
        [category.model_dump(mode="json", by_alias=True) for category in categories],
        meta={"total": len(categories)},
    )


@router.post("/sessions", status_code=201)
def create_exam_session(
    payload: ExamSessionCreate,
    service: ExamService = Depends(get_exam_service),
) -> dict[str, object]:
    try:
        session: ExamSessionRead = service.create_session(
            category_id=payload.category_id,
            question_count=payload.question_count,
        )
    except ExamCategoryNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return success_response(session.model_dump(mode="json", by_alias=True))


@router.post("/submissions")
def submit_exam_answer(
    payload: ExamSubmissionCreate,
    service: ExamGradingService = Depends(get_exam_grading_service),
    attempt_repository: ExamAttemptRepository = Depends(get_exam_attempt_repository),
    auth_context: AuthContext | None = Depends(get_optional_auth_context),
) -> dict[str, object]:
    try:
        submission: ExamSubmissionRead = service.grade_submission(
            lesson_id=payload.lesson_id,
            source_code=payload.source_code,
        )
    except ExecutionInputLimitError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (ExamLessonNotFoundError, ExamAssessmentNotConfiguredError) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    if auth_context is not None:
        attempt_repository.save_attempt(
            workspace_id=auth_context.workspace.id,
            source_code=payload.source_code,
            submission=submission,
        )

    return success_response(submission.model_dump(mode="json", by_alias=True))
