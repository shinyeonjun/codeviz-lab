from app.modules.learning.domain.catalog import (
    LEARNING_CATEGORY_CATALOG,
    LEARNING_LESSON_CATALOG,
)
from app.modules.learning.domain.exceptions import LearningLessonNotFoundError
from app.modules.learning.presentation.http.schemas import (
    LearningCategoryRead,
    LearningLessonRead,
    LearningLessonSummaryRead,
)


class LearningService:
    def __init__(self) -> None:
        self._categories = [
            LearningCategoryRead.model_validate(
                item | {"lesson_count": 0, "visualization_modes": []}
            )
            for item in LEARNING_CATEGORY_CATALOG
        ]
        self._lessons = [
            LearningLessonRead.model_validate(self._enrich_lesson(item))
            for item in LEARNING_LESSON_CATALOG
        ]

    def get_categories(self) -> list[LearningCategoryRead]:
        category_map = {
            category.id: {
                "lesson_count": 0,
                "visualization_modes": set(),
            }
            for category in self._categories
        }

        for lesson in self._lessons:
            category_stats = category_map[lesson.category_id]
            category_stats["lesson_count"] += 1
            category_stats["visualization_modes"].add(lesson.visualization_mode)

        return [
            category.model_copy(
                update={
                    "lesson_count": category_map[category.id]["lesson_count"],
                    "visualization_modes": sorted(category_map[category.id]["visualization_modes"]),
                }
            )
            for category in sorted(self._categories, key=lambda item: item.order)
        ]

    def get_lessons(
        self,
        *,
        category_id: str | None = None,
        visualization_mode: str | None = None,
        language: str | None = None,
    ) -> list[LearningLessonSummaryRead]:
        filtered_lessons = self._lessons
        if category_id is not None:
            filtered_lessons = [lesson for lesson in filtered_lessons if lesson.category_id == category_id]
        if visualization_mode is not None:
            filtered_lessons = [
                lesson for lesson in filtered_lessons if lesson.visualization_mode == visualization_mode
            ]
        if language is not None:
            filtered_lessons = [lesson for lesson in filtered_lessons if lesson.language == language]

        return [
            LearningLessonSummaryRead.model_validate(lesson.model_dump())
            for lesson in filtered_lessons
        ]

    def get_lesson(self, lesson_id: str) -> LearningLessonRead:
        for lesson in self._lessons:
            if lesson.id == lesson_id:
                return lesson
        raise LearningLessonNotFoundError(lesson_id)

    def _enrich_lesson(self, raw_item: dict[str, object]) -> dict[str, object]:
        category_name = next(
            category["name"]
            for category in LEARNING_CATEGORY_CATALOG
            if category["id"] == raw_item["category_id"]
        )
        category_lessons = [
            lesson for lesson in LEARNING_LESSON_CATALOG if lesson["category_id"] == raw_item["category_id"]
        ]
        category_ids = [str(lesson["id"]) for lesson in category_lessons]
        current_index = category_ids.index(str(raw_item["id"]))

        previous_lesson_id = category_ids[current_index - 1] if current_index > 0 else None
        next_lesson_id = category_ids[current_index + 1] if current_index < len(category_ids) - 1 else None

        related_lesson_ids: list[str] = [
            lesson_id
            for lesson_id in category_ids
            if lesson_id != raw_item["id"]
        ]

        same_visualization_ids = [
            str(lesson["id"])
            for lesson in LEARNING_LESSON_CATALOG
            if lesson["id"] != raw_item["id"]
            and lesson["visualization_mode"] == raw_item["visualization_mode"]
        ]
        for lesson_id in same_visualization_ids:
            if lesson_id not in related_lesson_ids:
                related_lesson_ids.append(lesson_id)

        return raw_item | {
            "category_name": category_name,
            "learning_content": self._build_learning_content(raw_item),
            "implementation_challenge": self._build_implementation_challenge(raw_item),
            "previous_lesson_id": previous_lesson_id,
            "next_lesson_id": next_lesson_id,
            "related_lesson_ids": related_lesson_ids[:4],
        }

    def _build_learning_content(self, raw_item: dict[str, object]) -> dict[str, object]:
        return {
            "title": "학습",
            "summary": str(raw_item["description"]),
            "concept_points": [str(point) for point in raw_item["learning_points"]],
            "walkthrough_code": str(raw_item["source_code"]),
        }

    def _build_implementation_challenge(self, raw_item: dict[str, object]) -> dict[str, object]:
        exercise = raw_item.get("exercise")
        if isinstance(exercise, dict):
            return {
                "title": "직접 구현",
                "prompt": str(exercise["prompt"]),
                "starter_code": str(exercise["starter_code"]),
                "checkpoints": [str(point) for point in exercise.get("checkpoints", [])],
            }

        title = str(raw_item["title"])
        description = str(raw_item["description"])
        checkpoints = [str(point) for point in raw_item["learning_points"]]
        return {
            "title": "직접 구현",
            "prompt": f"{title} 주제를 직접 구현해 보세요. {description}",
            "starter_code": "# 여기서부터 직접 구현해 보세요.\n",
            "checkpoints": checkpoints,
        }


def get_learning_service() -> LearningService:
    return LearningService()
