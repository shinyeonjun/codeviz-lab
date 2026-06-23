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
from app.modules.learning.application.services.learning_service import LearningService
from app.modules.learning.domain.catalog import (
    LEARNING_CATEGORY_CATALOG,
    LEARNING_LESSON_CATALOG,
)
from app.modules.learning.infrastructure.persistence.repository import LearningProgressRepository


class ExamService:
    def __init__(
        self,
        learning_service: LearningService | None = None,
        progress_repository: LearningProgressRepository | None = None,
    ) -> None:
        self._learning_service = learning_service or LearningService()
        self._progress_repository = progress_repository
        self._category_map = {
            str(category["id"]): dict(category)
            for category in LEARNING_CATEGORY_CATALOG
        }
        self._lesson_map = {
            str(lesson["id"]): dict(lesson)
            for lesson in LEARNING_LESSON_CATALOG
        }

    def get_categories(
        self,
        *,
        user_id: str | None = None,
        language: str | None = None,
    ) -> list[ExamCategoryRead]:
        learned_lesson_ids = self._get_learned_lesson_ids(user_id)
        return [
            ExamCategoryRead(
                id=category.id,
                name=category.name,
                description=category.description,
                question_count=len(
                    self._get_exam_lesson_pool(
                        category.id,
                        learned_lesson_ids=learned_lesson_ids,
                        language=language,
                    )
                ),
            )
            for category in self._learning_service.get_categories()
            if self._get_exam_lesson_pool(
                category.id,
                learned_lesson_ids=learned_lesson_ids,
                language=language,
            )
        ]

    def create_session(
        self,
        *,
        user_id: str | None = None,
        category_id: str,
        question_count: int,
        language: str = "python",
    ) -> ExamSessionRead:
        learned_lesson_ids = self._get_learned_lesson_ids(user_id)
        categories = {
            category.id: category
            for category in self.get_categories(user_id=user_id, language=language)
        }
        category = categories.get(category_id)
        if category is None:
            raise ExamCategoryNotFoundError(category_id)

        lesson_pool = self._get_exam_lesson_pool(
            category_id,
            learned_lesson_ids=learned_lesson_ids,
            language=language,
        )
        if not lesson_pool:
            raise ExamCategoryNotFoundError(category_id)
        selected_lessons = random.sample(
            lesson_pool,
            k=min(question_count, len(lesson_pool)),
        )
        questions = [
            self._build_question(lesson, language=language)
            for lesson in selected_lessons
        ]

        return ExamSessionRead(
            session_id=f"exam-{uuid.uuid4().hex[:12]}",
            category_id=category.id,
            category_name=category.name,
            language=language,
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

    def _get_exam_lesson_pool(
        self,
        category_id: str,
        *,
        learned_lesson_ids: set[str] | None = None,
        language: str | None = None,
    ) -> list[dict[str, object]]:
        lessons = [
            lesson
            for lesson in self._lesson_map.values()
            if str(lesson["category_id"]) == category_id
            and isinstance(lesson.get("exercise"), dict)
            and lesson.get("exam_enabled", True) is not False
            and (learned_lesson_ids is None or str(lesson["id"]) in learned_lesson_ids)
            and self._supports_language(lesson, language)
        ]
        if not lessons:
            return []
        return lessons

    def _get_learned_lesson_ids(self, user_id: str | None) -> set[str] | None:
        if user_id is None or self._progress_repository is None:
            return None
        return self._progress_repository.list_lesson_ids_by_user(user_id)

    def _supports_language(self, lesson: dict[str, object], language: str | None) -> bool:
        if language is None:
            return True
        supported_languages = lesson.get("supported_languages")
        if isinstance(supported_languages, list):
            return language in {str(item) for item in supported_languages}
        return language in {"python", "c", "java"}

    def _get_raw_lesson(self, lesson_id: str) -> dict[str, object]:
        lesson = self._lesson_map.get(lesson_id)
        if lesson is None:
            raise ExamLessonNotFoundError(lesson_id)
        return lesson

    def _build_question(self, lesson: dict[str, object], *, language: str) -> ExamQuestionRead:
        exercise = lesson.get("exercise") if isinstance(lesson.get("exercise"), dict) else {}
        category = self._category_map[str(lesson["category_id"])]
        return ExamQuestionRead(
            id=f"question-{lesson['id']}",
            lesson_id=str(lesson["id"]),
            category_id=str(lesson["category_id"]),
            category_name=str(category["name"]),
            title=str(lesson["title"]),
            prompt=str(exercise.get("prompt", lesson["description"])),
            language=language,
            visualization_mode=str(lesson["visualization_mode"]),
            starter_code=self._build_starter_code(exercise=exercise, language=language),
            difficulty=str(lesson["difficulty"]),
            estimated_minutes=int(lesson["estimated_minutes"]),
            tags=[str(tag) for tag in lesson["tags"]],
        )

    def _build_starter_code(self, *, exercise: object, language: str) -> str:
        if not isinstance(exercise, dict):
            function_name = "solve"
        else:
            if language == "python":
                return str(exercise.get("starter_code", "# 여기서부터 코드를 작성하세요.\n"))
            function_name = str(exercise.get("function_name", "solve"))

        if language == "c":
            return self._build_c_starter(function_name)
        if language == "java":
            return self._build_java_starter(function_name)
        return "# 여기서부터 코드를 작성하세요.\n"

    def _build_c_starter(self, function_name: str) -> str:
        return (
            "#include <stdio.h>\n\n"
            f"int {function_name}(void) {{\n"
            "    // 여기에 풀이를 작성하세요.\n"
            "    return 0;\n"
            "}\n\n"
            "int main(void) {\n"
            f"    printf(\"%d\\n\", {function_name}());\n"
            "    return 0;\n"
            "}\n"
        )

    def _build_java_starter(self, function_name: str) -> str:
        return (
            "import java.util.*;\n\n"
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            f"        System.out.println({function_name}());\n"
            "    }\n\n"
            f"    public static Object {function_name}() {{\n"
            "        // 여기에 풀이를 작성하세요.\n"
            "        return null;\n"
            "    }\n"
            "}\n"
        )


def get_exam_service() -> ExamService:
    return ExamService()
