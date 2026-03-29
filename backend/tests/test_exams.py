def test_read_exam_categories(client):
    response = client.get("/api/v1/exams/categories")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["meta"]["total"] >= 1
    assert all("questionCount" in category for category in payload["data"])


def test_create_exam_session_returns_random_questions_from_category(client):
    response = client.post(
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


def test_create_exam_session_when_category_missing_returns_404(client):
    response = client.post(
        "/api/v1/exams/sessions",
        json={"categoryId": "missing-category", "questionCount": 2},
    )

    assert response.status_code == 404
    assert "시험 카테고리를 찾을 수 없습니다" in response.json()["detail"]


def test_submit_exam_answer_returns_score_for_correct_code(client):
    response = client.post(
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


def test_submit_exam_answer_returns_failed_score_for_wrong_code(client):
    response = client.post(
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


def test_submit_exam_answer_returns_error_for_invalid_code(client):
    response = client.post(
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


def test_submit_exam_answer_handles_surrogate_stdout_without_crashing(client):
    response = client.post(
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
