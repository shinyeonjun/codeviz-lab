import random
import uuid

from app.modules.exams.domain.exceptions import (
    ExamAssessmentNotConfiguredError,
    ExamCategoryNotFoundError,
    ExamLessonNotFoundError,
)
from app.modules.exams.presentation.http.schemas import (
    ExamCategoryRead,
    ExamQuestionRead,
    ExamSessionRead,
)
from app.modules.learning.domain.catalog import (
    LEARNING_CATEGORY_CATALOG,
    LEARNING_LESSON_CATALOG,
)
from app.modules.learning.application.services.learning_service import LearningService


class ExamService:
    def __init__(self, learning_service: LearningService | None = None) -> None:
        self._learning_service = learning_service or LearningService()
        self._category_map = {
            str(category["id"]): dict(category)
            for category in LEARNING_CATEGORY_CATALOG
        }
        self._lesson_map = {
            str(lesson["id"]): dict(lesson)
            for lesson in LEARNING_LESSON_CATALOG
        }

    def get_categories(self) -> list[ExamCategoryRead]:
        return [
            ExamCategoryRead(
                id=category.id,
                name=category.name,
                description=category.description,
                question_count=category.lesson_count,
            )
            for category in self._learning_service.get_categories()
            if category.lesson_count > 0
        ]

    def create_session(self, *, category_id: str, question_count: int) -> ExamSessionRead:
        categories = {category.id: category for category in self.get_categories()}
        category = categories.get(category_id)
        if category is None:
            raise ExamCategoryNotFoundError(category_id)

        lesson_pool = self._get_exam_lesson_pool(category_id)
        selected_lessons = random.sample(
            lesson_pool,
            k=min(question_count, len(lesson_pool)),
        )

        questions = [self._build_question(lesson) for lesson in selected_lessons]

        return ExamSessionRead(
            session_id=f"exam-{uuid.uuid4().hex[:12]}",
            category_id=category.id,
            category_name=category.name,
            question_count=len(questions),
            questions=questions,
        )

    def get_assessment_definition(self, lesson_id: str) -> dict[str, object]:
        lesson = self._get_raw_lesson(lesson_id)
        exercise = lesson.get("exercise")
        if not isinstance(exercise, dict):
            raise ExamAssessmentNotConfiguredError(lesson_id)
        return {
            "lesson_id": lesson_id,
            "question_id": f"question-{lesson_id}",
            "function_name": str(exercise["function_name"]),
            "prompt": str(exercise["prompt"]),
            "starter_code": str(exercise["starter_code"]),
            "test_cases": [dict(case) for case in exercise.get("test_cases", [])],
        }

    def _get_exam_lesson_pool(self, category_id: str) -> list[dict[str, object]]:
        lessons = [
            lesson
            for lesson in self._lesson_map.values()
            if str(lesson["category_id"]) == category_id
            and isinstance(lesson.get("exercise"), dict)
        ]
        if not lessons:
            raise ExamCategoryNotFoundError(category_id)
        return lessons

    def _get_raw_lesson(self, lesson_id: str) -> dict[str, object]:
        lesson = self._lesson_map.get(lesson_id)
        if lesson is None:
            raise ExamLessonNotFoundError(lesson_id)
        return lesson

    def _build_question(self, lesson: dict[str, object]) -> ExamQuestionRead:
        exercise = lesson.get("exercise") if isinstance(lesson.get("exercise"), dict) else {}
        category = self._category_map[str(lesson["category_id"])]
        return ExamQuestionRead(
            id=f"question-{lesson['id']}",
            lesson_id=str(lesson["id"]),
            category_id=str(lesson["category_id"]),
            category_name=str(category["name"]),
            title=str(lesson["title"]),
            prompt=str(exercise.get("prompt", lesson["description"])),
            visualization_mode=str(lesson["visualization_mode"]),
            starter_code=str(exercise.get("starter_code", "# 여기에 코드를 작성하세요.\n")),
            difficulty=str(lesson["difficulty"]),
            estimated_minutes=int(lesson["estimated_minutes"]),
            tags=[str(tag) for tag in lesson["tags"]],
        )


def get_exam_service() -> ExamService:
    return ExamService()
