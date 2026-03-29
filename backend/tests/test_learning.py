def test_read_learning_categories(client):
    response = client.get("/api/v1/learning/categories")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert len(payload["data"]) >= 3
    assert any(category["id"] == "algorithms" for category in payload["data"])
    assert all("lessonCount" in category for category in payload["data"])


def test_read_learning_lessons_with_category_filter(client):
    response = client.get(
        "/api/v1/learning/lessons",
        params={"categoryId": "data-structures", "language": "python"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["meta"]["total"] >= 1
    assert all(lesson["categoryId"] == "data-structures" for lesson in payload["data"])


def test_read_learning_lessons_with_visualization_filter(client):
    response = client.get(
        "/api/v1/learning/lessons",
        params={"visualizationMode": "array-bars"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["meta"]["total"] >= 1
    assert all(lesson["visualizationMode"] == "array-bars" for lesson in payload["data"])


def test_read_learning_lesson_detail(client):
    response = client.get("/api/v1/learning/lessons/lesson-insertion-sort")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["id"] == "lesson-insertion-sort"
    assert payload["data"]["visualizationMode"] == "array-bars"
    assert "sourceCode" in payload["data"]
    assert payload["data"]["learningContent"]["title"] == "학습"
    assert payload["data"]["implementationChallenge"]["title"] == "직접 구현"
    assert payload["data"]["implementationChallenge"]["starterCode"].startswith("def insertion_sort")
    assert payload["data"]["previousLessonId"] is None
    assert payload["data"]["nextLessonId"] == "lesson-dp-table"
    assert "lesson-dp-table" in payload["data"]["relatedLessonIds"]


def test_read_learning_lesson_detail_from_additional_catalog(client):
    response = client.get("/api/v1/learning/lessons/lesson-graph-bipartite-check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["id"] == "lesson-graph-bipartite-check"
    assert payload["data"]["visualizationMode"] == "graph-bipartite-check"
    assert payload["data"]["implementationChallenge"]["starterCode"].startswith("def is_bipartite")


def test_read_learning_lesson_detail_when_missing_returns_404(client):
    response = client.get("/api/v1/learning/lessons/missing-lesson")

    assert response.status_code == 404
    assert "학습 콘텐츠를 찾을 수 없습니다" in response.json()["detail"]
