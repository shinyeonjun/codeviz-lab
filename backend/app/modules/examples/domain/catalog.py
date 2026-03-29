from app.modules.learning.domain.catalog import (
    LEARNING_CATEGORY_CATALOG,
    LEARNING_LESSON_CATALOG,
)


def _build_category_name_map() -> dict[str, str]:
    return {
        str(category["id"]): str(category["name"])
        for category in LEARNING_CATEGORY_CATALOG
    }


def _build_example_catalog() -> list[dict[str, object]]:
    category_name_map = _build_category_name_map()
    catalog: list[dict[str, object]] = []

    for lesson in LEARNING_LESSON_CATALOG:
        category_id = str(lesson["category_id"])
        catalog.append(
            {
                "id": str(lesson["id"]),
                "title": str(lesson["title"]),
                "category": category_name_map.get(category_id, category_id),
                "description": str(lesson["description"]),
                "language": str(lesson["language"]),
                "source_code": str(lesson["source_code"]),
                "focus_points": [str(point) for point in lesson.get("learning_points", [])],
            }
        )

    return catalog


EXAMPLE_CATALOG: list[dict[str, object]] = _build_example_catalog()
