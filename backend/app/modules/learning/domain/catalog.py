import json
from functools import lru_cache
from pathlib import Path


DATA_DIR = Path(__file__).with_name("data")


def _load_catalog_file(file_name: str) -> list[dict[str, object]]:
    payload = json.loads((DATA_DIR / file_name).read_text(encoding="utf-8"))
    return [dict(item) for item in payload]


@lru_cache
def get_learning_category_catalog() -> list[dict[str, object]]:
    return _load_catalog_file("categories.json")


@lru_cache
def get_learning_lesson_catalog() -> list[dict[str, object]]:
    return (
        _load_catalog_file("lessons.json")
        + _load_catalog_file("lessons_extra.json")
        + _load_catalog_file("lessons_more.json")
    )


LEARNING_CATEGORY_CATALOG = get_learning_category_catalog()
LEARNING_LESSON_CATALOG = get_learning_lesson_catalog()
