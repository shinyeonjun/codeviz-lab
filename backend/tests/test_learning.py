import pytest

from app.modules.learning.domain.catalog import LEARNING_CATEGORY_CATALOG, LEARNING_LESSON_CATALOG


def _flatten_text_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _flatten_text_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_text_values(item)
    elif isinstance(value, str):
        yield value


@pytest.mark.no_db
def test_learning_catalog_keeps_core_lessons_polished():
    category_ids = {str(category["id"]) for category in LEARNING_CATEGORY_CATALOG}

    assert len(LEARNING_LESSON_CATALOG) >= 30

    for lesson in LEARNING_LESSON_CATALOG:
        assert lesson["category_id"] in category_ids
        assert str(lesson["title"]).strip()
        assert str(lesson["description"]).strip()
        assert str(lesson["source_code"]).strip()
        assert lesson["learning_points"]
        assert lesson["tags"]

        exercise = lesson.get("exercise")
        assert isinstance(exercise, dict)
        assert str(exercise["prompt"]).strip()
        assert str(exercise["starter_code"]).strip()
        assert str(exercise["function_name"]).strip()
        assert exercise["checkpoints"]
        assert exercise["test_cases"]

        for text in _flatten_text_values(lesson):
            assert "\ufffd" not in text
            assert "???" not in text
            assert not any(0x4E00 <= ord(character) <= 0x9FFF for character in text)


@pytest.mark.no_db
def test_basic_lessons_follow_beginner_learning_order():
    expected_lesson_modes = [
        ("lesson-data-types", "array-cells"),
        ("lesson-variable-flow", "array-cells"),
        ("lesson-operator-precedence", "flowchart"),
        ("lesson-input-parsing", "array-cells"),
        ("lesson-comparison-if", "flowchart"),
        ("lesson-if-else-branch", "flowchart"),
        ("lesson-logical-operators", "flowchart"),
        ("lesson-switch-match", "flowchart"),
        ("lesson-list-indexing", "array-cells"),
        ("lesson-for-loop-sum", "flowchart"),
        ("lesson-while-loop-counter", "flowchart"),
        ("lesson-nested-loops", "flowchart"),
        ("lesson-dictionary-basics", "array-cells"),
        ("lesson-set-basics", "array-cells"),
        ("lesson-function-parameters", "call-stack"),
        ("lesson-function-return", "call-stack"),
        ("lesson-lambda-functions", "call-stack"),
        ("lesson-exception-handling", "flowchart"),
        ("lesson-file-io-basics", "flowchart"),
        ("lesson-class-object", "array-cells"),
        ("lesson-inheritance", "call-stack"),
        ("lesson-pointer-concept-c", "array-cells"),
    ]
    basic_lessons = [
        lesson for lesson in LEARNING_LESSON_CATALOG if lesson["category_id"] == "basics"
    ]

    assert [lesson["id"] for lesson in basic_lessons] == [
        lesson_id for lesson_id, _ in expected_lesson_modes
    ]
    assert {
        lesson["id"]: lesson["visualization_mode"] for lesson in basic_lessons
    } == dict(expected_lesson_modes)


def test_read_learning_categories(authenticated_client):
    response = authenticated_client.get("/api/v1/learning/categories")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert len(payload["data"]) >= 3
    assert any(category["id"] == "algorithms" for category in payload["data"])
    assert all("lessonCount" in category for category in payload["data"])


def test_read_learning_lessons_with_category_filter(authenticated_client):
    response = authenticated_client.get(
        "/api/v1/learning/lessons",
        params={"categoryId": "data-structures", "language": "python"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["meta"]["total"] >= 1
    assert all(lesson["categoryId"] == "data-structures" for lesson in payload["data"])


def test_read_learning_lessons_with_visualization_filter(authenticated_client):
    response = authenticated_client.get(
        "/api/v1/learning/lessons",
        params={"visualizationMode": "array-bars"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["meta"]["total"] >= 1
    assert all(lesson["visualizationMode"] == "array-bars" for lesson in payload["data"])


def test_read_learning_lesson_detail(authenticated_client):
    response = authenticated_client.get("/api/v1/learning/lessons/lesson-insertion-sort")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["id"] == "lesson-insertion-sort"
    assert payload["data"]["visualizationMode"] == "array-bars"
    assert "sourceCode" in payload["data"]
    assert payload["data"]["learningContent"]["title"] == "학습"
    assert payload["data"]["implementationChallenge"]["title"] == "직접 구현"
    assert payload["data"]["implementationChallenge"]["starterCode"].startswith("def insertion_sort")
    assert payload["data"]["previousLessonId"] == "lesson-selection-sort"
    assert payload["data"]["nextLessonId"] == "lesson-bubble-sort"
    assert "lesson-selection-sort" in payload["data"]["relatedLessonIds"]


def test_read_learning_lesson_detail_from_additional_catalog(authenticated_client):
    response = authenticated_client.get("/api/v1/learning/lessons/lesson-graph-adjacency-list")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["id"] == "lesson-graph-adjacency-list"
    assert payload["data"]["visualizationMode"] == "graph-node-edge"
    assert payload["data"]["implementationChallenge"]["starterCode"].startswith("def build_graph")


def test_language_specific_lessons_expose_supported_languages(authenticated_client):
    pointer_response = authenticated_client.get("/api/v1/learning/lessons/lesson-pointer-concept-c")
    lambda_response = authenticated_client.get("/api/v1/learning/lessons/lesson-lambda-functions")

    assert pointer_response.status_code == 200
    assert lambda_response.status_code == 200
    assert pointer_response.json()["data"]["language"] == "c"
    assert pointer_response.json()["data"]["supportedLanguages"] == ["c"]
    assert lambda_response.json()["data"]["supportedLanguages"] == ["python", "java"]


def test_mark_learning_lesson_progress_updates_catalog(authenticated_client):
    before_response = authenticated_client.get(
        "/api/v1/learning/lessons",
        params={"categoryId": "basics"},
    )
    assert before_response.status_code == 200
    before_lessons = before_response.json()["data"]
    target_before = next(lesson for lesson in before_lessons if lesson["id"] == "lesson-data-types")
    assert target_before["progress"] is None

    progress_response = authenticated_client.post(
        "/api/v1/learning/lessons/lesson-data-types/progress"
    )
    assert progress_response.status_code == 200
    progress = progress_response.json()["data"]
    assert progress["lessonId"] == "lesson-data-types"
    assert progress["status"] == "studied"
    assert progress["studyCount"] == 1
    assert progress["totalStudySeconds"] == 0
    assert progress["firstStudiedAt"]
    assert progress["lastStudiedAt"]

    second_progress_response = authenticated_client.post(
        "/api/v1/learning/lessons/lesson-data-types/progress"
    )
    assert second_progress_response.status_code == 200
    assert second_progress_response.json()["data"]["studyCount"] == 2

    after_response = authenticated_client.get(
        "/api/v1/learning/lessons",
        params={"categoryId": "basics"},
    )
    assert after_response.status_code == 200
    after_lessons = after_response.json()["data"]
    target_after = next(lesson for lesson in after_lessons if lesson["id"] == "lesson-data-types")
    assert target_after["progress"]["lessonId"] == "lesson-data-types"
    assert target_after["progress"]["studyCount"] == 2


def test_read_learning_insights_returns_progress_and_recommendations(authenticated_client):
    authenticated_client.post("/api/v1/learning/lessons/lesson-data-types/progress")

    response = authenticated_client.get("/api/v1/learning/insights")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["totalLessons"] >= 30
    assert payload["studiedLessons"] == 1
    assert payload["completionRate"] > 0
    assert payload["categoryProgress"]
    assert payload["weakCategories"]
    assert payload["nextRecommendations"]
    assert payload["dailyRecommendation"]["lesson"]["id"]
    assert payload["reviewRecommendations"][0]["lesson"]["id"] == "lesson-data-types"


def test_read_learning_lesson_detail_when_missing_returns_404(authenticated_client):
    response = authenticated_client.get("/api/v1/learning/lessons/missing-lesson")

    assert response.status_code == 404
    assert "학습 콘텐츠를 찾을 수 없습니다" in response.json()["detail"]
