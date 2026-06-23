from app.modules.learning.domain.catalog import (
    LEARNING_CATEGORY_CATALOG,
    LEARNING_LESSON_CATALOG,
)
from app.modules.learning.domain.exceptions import LearningLessonNotFoundError
from app.modules.learning.infrastructure.persistence.models import UserLessonProgress
from app.modules.learning.infrastructure.persistence.repository import LearningProgressRepository
from app.modules.learning.presentation.http.schemas import (
    LearningCategoryProgressRead,
    LearningCategoryRead,
    LearningInsightRead,
    LearningLessonRead,
    LearningRecommendationRead,
    LearningProgressRead,
    LearningLessonSummaryRead,
)


class LearningService:
    def __init__(self, *, progress_repository: LearningProgressRepository | None = None) -> None:
        self._progress_repository = progress_repository
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
        user_id: str,
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

        progress_by_lesson_id = self._get_progress_by_lesson_id(user_id)
        return [
            LearningLessonSummaryRead.model_validate(
                lesson.model_dump() | {"progress": progress_by_lesson_id.get(lesson.id)}
            )
            for lesson in filtered_lessons
        ]

    def get_lesson(self, lesson_id: str, *, user_id: str | None = None) -> LearningLessonRead:
        progress_by_lesson_id = self._get_progress_by_lesson_id(user_id) if user_id else {}
        for lesson in self._lessons:
            if lesson.id == lesson_id:
                return LearningLessonRead.model_validate(
                    lesson.model_dump() | {"progress": progress_by_lesson_id.get(lesson.id)}
                )
        raise LearningLessonNotFoundError(lesson_id)

    def mark_lesson_studied(self, *, user_id: str, lesson_id: str) -> LearningProgressRead:
        if self._progress_repository is None:
            raise RuntimeError("Learning progress repository is required.")
        self.get_lesson(lesson_id)
        progress = self._progress_repository.mark_studied(
            user_id=user_id,
            lesson_id=lesson_id,
        )
        return self._build_progress_read(progress)

    def get_insights(self, *, user_id: str) -> LearningInsightRead:
        progress_by_lesson_id = self._get_progress_by_lesson_id(user_id)
        lesson_summaries = [
            LearningLessonSummaryRead.model_validate(
                lesson.model_dump() | {"progress": progress_by_lesson_id.get(lesson.id)}
            )
            for lesson in self._lessons
        ]
        lessons_by_id = {lesson.id: lesson for lesson in lesson_summaries}
        studied_ids = set(progress_by_lesson_id)
        category_progress = self._build_category_progress(studied_ids)
        weak_categories = [
            progress
            for progress in sorted(
                category_progress,
                key=lambda item: (item.completion_rate, item.studied_count, item.total_count),
            )
            if progress.studied_count < progress.total_count
        ][:3]
        next_recommendations = self._build_next_recommendations(
            category_progress=category_progress,
            lessons_by_id=lessons_by_id,
        )
        review_recommendations = self._build_review_recommendations(
            progress_by_lesson_id=progress_by_lesson_id,
            lessons_by_id=lessons_by_id,
        )

        return LearningInsightRead.model_validate(
            {
                "total_lessons": len(self._lessons),
                "studied_lessons": len(studied_ids),
                "completion_rate": self._completion_rate(len(studied_ids), len(self._lessons)),
                "category_progress": category_progress,
                "weak_categories": weak_categories,
                "next_recommendations": next_recommendations,
                "review_recommendations": review_recommendations,
                "daily_recommendation": next_recommendations[0] if next_recommendations else None,
            }
        )

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
    def _build_category_progress(self, studied_ids: set[str]) -> list[LearningCategoryProgressRead]:
        progress_items: list[LearningCategoryProgressRead] = []
        for category in sorted(self._categories, key=lambda item: item.order):
            lessons = [lesson for lesson in self._lessons if lesson.category_id == category.id]
            studied_count = sum(1 for lesson in lessons if lesson.id in studied_ids)
            next_lesson = next((lesson for lesson in lessons if lesson.id not in studied_ids), None)
            progress_items.append(
                LearningCategoryProgressRead.model_validate(
                    {
                        "category_id": category.id,
                        "category_name": category.name,
                        "studied_count": studied_count,
                        "total_count": len(lessons),
                        "completion_rate": self._completion_rate(studied_count, len(lessons)),
                        "next_lesson_id": next_lesson.id if next_lesson else None,
                    }
                )
            )
        return progress_items

    def _build_next_recommendations(
        self,
        *,
        category_progress: list[LearningCategoryProgressRead],
        lessons_by_id: dict[str, LearningLessonSummaryRead],
    ) -> list[LearningRecommendationRead]:
        recommendations: list[LearningRecommendationRead] = []
        for progress in sorted(category_progress, key=lambda item: (item.completion_rate, item.total_count)):
            if progress.next_lesson_id is None:
                continue
            lesson = lessons_by_id.get(progress.next_lesson_id)
            if lesson is None:
                continue
            recommendations.append(
                LearningRecommendationRead(
                    lesson=lesson,
                    reason=f"{progress.category_name}에서 아직 학습하지 않은 다음 순서입니다.",
                )
            )
        return recommendations[:3]

    def _build_review_recommendations(
        self,
        *,
        progress_by_lesson_id: dict[str, LearningProgressRead],
        lessons_by_id: dict[str, LearningLessonSummaryRead],
    ) -> list[LearningRecommendationRead]:
        review_targets = sorted(
            progress_by_lesson_id.values(),
            key=lambda item: (item.study_count, item.last_studied_at),
        )
        recommendations: list[LearningRecommendationRead] = []
        for progress in review_targets:
            lesson = lessons_by_id.get(progress.lesson_id)
            if lesson is None:
                continue
            recommendations.append(
                LearningRecommendationRead(
                    lesson=lesson,
                    reason="학습 횟수가 적거나 오래 전에 본 내용이라 복습하면 좋습니다.",
                )
            )
        return recommendations[:3]

    def _completion_rate(self, studied_count: int, total_count: int) -> float:
        if total_count <= 0:
            return 0.0
        return round(studied_count / total_count, 4)

    def _get_progress_by_lesson_id(self, user_id: str) -> dict[str, LearningProgressRead]:
        if self._progress_repository is None:
            return {}
        return {
            progress.lesson_id: self._build_progress_read(progress)
            for progress in self._progress_repository.list_by_user(user_id)
        }

    def _build_progress_read(self, progress: UserLessonProgress) -> LearningProgressRead:
        return LearningProgressRead.model_validate(
            {
                "lesson_id": progress.lesson_id,
                "status": progress.status,
                "first_studied_at": progress.first_studied_at,
                "last_studied_at": progress.last_studied_at,
                "study_count": progress.study_count,
                "total_study_seconds": progress.total_study_seconds,
                "completed_at": progress.completed_at,
            }
        )


def get_learning_service() -> LearningService:
    return LearningService()
