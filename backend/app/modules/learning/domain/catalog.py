import json
from functools import lru_cache
from pathlib import Path


DATA_DIR = Path(__file__).with_name("data")

BASICS_LESSON_ORDER = (
    "lesson-data-types",
    "lesson-variable-flow",
    "lesson-operator-precedence",
    "lesson-input-parsing",
    "lesson-comparison-if",
    "lesson-if-else-branch",
    "lesson-logical-operators",
    "lesson-switch-match",
    "lesson-list-indexing",
    "lesson-for-loop-sum",
    "lesson-while-loop-counter",
    "lesson-nested-loops",
    "lesson-dictionary-basics",
    "lesson-set-basics",
    "lesson-function-parameters",
    "lesson-function-return",
    "lesson-lambda-functions",
    "lesson-exception-handling",
    "lesson-file-io-basics",
    "lesson-class-object",
    "lesson-inheritance",
    "lesson-pointer-concept-c",
)

BASICS_LESSON_ORDER_INDEX = {
    lesson_id: index for index, lesson_id in enumerate(BASICS_LESSON_ORDER)
}


def _load_catalog_file(file_name: str) -> list[dict[str, object]]:
    payload = json.loads((DATA_DIR / file_name).read_text(encoding="utf-8"))
    return [dict(item) for item in payload]


def _sort_lesson_catalog(lessons: list[dict[str, object]]) -> list[tuple[int, dict[str, object]]]:
    return sorted(
        enumerate(lessons),
        key=lambda item: _lesson_catalog_sort_key(item[0], item[1]),
    )


def _lesson_catalog_sort_key(original_index: int, lesson: dict[str, object]) -> tuple[int, int]:
    if lesson.get("category_id") == "basics":
        lesson_id = str(lesson["id"])
        return (0, BASICS_LESSON_ORDER_INDEX.get(lesson_id, len(BASICS_LESSON_ORDER) + original_index))
    return (original_index + 1, original_index)


@lru_cache
def get_learning_category_catalog() -> list[dict[str, object]]:
    return _load_catalog_file("categories.json")


@lru_cache
def get_learning_lesson_catalog() -> list[dict[str, object]]:
    lessons = (
        _load_catalog_file("lessons.json")
        + _load_catalog_file("lessons_extra.json")
        + _load_catalog_file("lessons_more.json")
        + _load_catalog_file("lessons_extended.json")
    )
    return [lesson for _, lesson in _sort_lesson_catalog(lessons)]


LEARNING_CATEGORY_CATALOG = get_learning_category_catalog()
LEARNING_LESSON_CATALOG = get_learning_lesson_catalog()
