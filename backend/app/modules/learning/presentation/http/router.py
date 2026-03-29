from fastapi import APIRouter, Depends, HTTPException, Query

from app.common.responses import success_response
from app.modules.auth.application.dependencies import get_required_auth_context
from app.modules.auth.domain.context import AuthContext
from app.modules.learning.application.services.learning_service import (
    LearningService,
    get_learning_service,
)
from app.modules.learning.domain.exceptions import LearningLessonNotFoundError
from app.modules.learning.presentation.http.schemas import (
    LearningCategoryRead,
    LearningLessonRead,
    LearningLessonSummaryRead,
)

router = APIRouter()


@router.get("/categories")
def read_learning_categories(
    _: AuthContext = Depends(get_required_auth_context),
    service: LearningService = Depends(get_learning_service),
) -> dict[str, object]:
    categories: list[LearningCategoryRead] = service.get_categories()
    return success_response(
        [category.model_dump(mode="json", by_alias=True) for category in categories]
    )


@router.get("/lessons")
def read_learning_lessons(
    category_id: str | None = Query(default=None, alias="categoryId"),
    visualization_mode: str | None = Query(default=None, alias="visualizationMode"),
    language: str | None = Query(default=None),
    _: AuthContext = Depends(get_required_auth_context),
    service: LearningService = Depends(get_learning_service),
) -> dict[str, object]:
    lessons: list[LearningLessonSummaryRead] = service.get_lessons(
        category_id=category_id,
        visualization_mode=visualization_mode,
        language=language,
    )
    return success_response(
        [lesson.model_dump(mode="json", by_alias=True) for lesson in lessons],
        meta={"total": len(lessons)},
    )


@router.get("/lessons/{lesson_id}")
def read_learning_lesson(
    lesson_id: str,
    _: AuthContext = Depends(get_required_auth_context),
    service: LearningService = Depends(get_learning_service),
) -> dict[str, object]:
    try:
        lesson: LearningLessonRead = service.get_lesson(lesson_id)
    except LearningLessonNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return success_response(lesson.model_dump(mode="json", by_alias=True))
