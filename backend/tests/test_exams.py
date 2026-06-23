def _mark_lessons_studied(client, *lesson_ids: str) -> None:
    for lesson_id in lesson_ids:
        response = client.post(f"/api/v1/learning/lessons/{lesson_id}/progress")
        assert response.status_code == 200


def test_read_exam_categories(authenticated_client):
    _mark_lessons_studied(authenticated_client, "lesson-variable-flow", "lesson-insertion-sort")

    response = authenticated_client.get("/api/v1/exams/categories")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["meta"]["total"] >= 1
    assert all("questionCount" in category for category in payload["data"])
    assert {category["id"] for category in payload["data"]} == {"basics", "algorithms"}


def test_create_exam_session_returns_questions_from_studied_lessons_only(authenticated_client):
    _mark_lessons_studied(authenticated_client, "lesson-insertion-sort", "lesson-bubble-sort")

    response = authenticated_client.post(
        "/api/v1/exams/sessions",
        json={"categoryId": "algorithms", "questionCount": 2},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["categoryId"] == "algorithms"
    assert payload["data"]["questionCount"] == 2
    assert len(payload["data"]["questions"]) == 2
    assert all(question["categoryId"] == "algorithms" for question in payload["data"]["questions"])
    assert {
        question["lessonId"] for question in payload["data"]["questions"]
    } <= {"lesson-insertion-sort", "lesson-bubble-sort"}


def test_create_exam_session_can_request_java_questions(authenticated_client):
    _mark_lessons_studied(authenticated_client, "lesson-insertion-sort")

    response = authenticated_client.post(
        "/api/v1/exams/sessions",
        json={"categoryId": "algorithms", "questionCount": 1, "language": "java"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["data"]["language"] == "java"
    assert payload["data"]["questions"][0]["language"] == "java"
    assert "public class Main" in payload["data"]["questions"][0]["starterCode"]


def test_create_exam_session_can_request_c_questions(authenticated_client):
    _mark_lessons_studied(authenticated_client, "lesson-insertion-sort")

    response = authenticated_client.post(
        "/api/v1/exams/sessions",
        json={"categoryId": "algorithms", "questionCount": 1, "language": "c"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["data"]["language"] == "c"
    assert payload["data"]["questions"][0]["language"] == "c"
    assert "#include <stdio.h>" in payload["data"]["questions"][0]["starterCode"]


def test_create_exam_session_when_category_missing_returns_404(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/exams/sessions",
        json={"categoryId": "missing-category", "questionCount": 2},
    )

    assert response.status_code == 404
    assert "시험 카테고리를 찾을 수 없습니다" in response.json()["detail"]


def test_create_exam_session_when_category_has_no_studied_lessons_returns_404(authenticated_client):
    _mark_lessons_studied(authenticated_client, "lesson-variable-flow")

    response = authenticated_client.post(
        "/api/v1/exams/sessions",
        json={"categoryId": "algorithms", "questionCount": 2},
    )

    assert response.status_code == 404


def test_submit_exam_answer_returns_score_for_correct_code(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/exams/submissions",
        json={
            "lessonId": "lesson-insertion-sort",
            "sourceCode": (
                "def insertion_sort(numbers):\n"
                "    items = numbers[:]\n"
                "    for i in range(1, len(items)):\n"
                "        key = items[i]\n"
                "        j = i - 1\n"
                "        while j >= 0 and items[j] > key:\n"
                "            items[j + 1] = items[j]\n"
                "            j -= 1\n"
                "        items[j + 1] = key\n"
                "    return items\n"
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["status"] == "passed"
    assert payload["data"]["score"] == 100
    assert payload["data"]["passedCount"] == payload["data"]["totalCount"]


def test_submit_exam_answer_returns_failed_score_for_wrong_code(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/exams/submissions",
        json={
            "lessonId": "lesson-stack",
            "sourceCode": (
                "def build_stack():\n"
                "    stack = []\n"
                "    stack.append(1)\n"
                "    return stack\n"
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["status"] == "failed"
    assert payload["data"]["score"] < 100
    assert payload["data"]["passedCount"] < payload["data"]["totalCount"]


def test_submit_exam_answer_returns_error_for_invalid_code(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/exams/submissions",
        json={
            "lessonId": "lesson-variable-flow",
            "sourceCode": "def transform_value(value)\n    return value\n",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["status"] == "error"
    assert payload["data"]["score"] == 0
    assert payload["data"]["errorMessage"] is not None


def test_submit_exam_answer_returns_language_mismatch_message(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/exams/submissions",
        json={
            "lessonId": "lesson-variable-flow",
            "language": "python",
            "sourceCode": (
                "public class Main { "
                "public static void main(String[] args) { "
                "System.out.println(1); "
                "} "
                "}"
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["status"] == "error"
    assert "선택한 언어는 Python" in payload["data"]["errorMessage"]
    assert "Java 코드로 보입니다" in payload["data"]["errorMessage"]


def test_submit_exam_answer_handles_surrogate_stdout_without_crashing(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/exams/submissions",
        json={
            "lessonId": "lesson-variable-flow",
            "sourceCode": (
                "def transform_value(value):\n"
                "    print('\\udcbe')\n"
                "    return (value + 5) * 2\n"
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["status"] == "passed"
