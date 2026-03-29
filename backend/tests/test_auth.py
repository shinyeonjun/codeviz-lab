def test_ensure_guest_session_sets_cookie_and_returns_guest_workspace(client):
    response = client.post("/api/v1/auth/guest/ensure")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["isAuthenticated"] is False
    assert payload["data"]["isGuest"] is True
    assert payload["data"]["currentWorkspace"]["isGuest"] is True
    assert "codeviz_session" in response.cookies


def test_register_user_claims_guest_workspace(client):
    client.post("/api/v1/auth/guest/ensure")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "tester@example.com",
            "password": "strongpass123",
            "name": "테스터",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["isAuthenticated"] is True
    assert payload["data"]["isGuest"] is False
    assert payload["data"]["user"]["email"] == "tester@example.com"
    assert payload["data"]["currentWorkspace"]["title"] == "테스터의 작업공간"


def test_create_and_select_workspace_for_authenticated_user(client):
    client.post("/api/v1/auth/register", json={
        "email": "workspace@example.com",
        "password": "strongpass123",
        "name": "워크스페이스",
    })

    create_response = client.post(
        "/api/v1/auth/workspaces",
        json={"title": "두 번째 작업공간"},
    )

    assert create_response.status_code == 201
    created_payload = create_response.json()
    assert created_payload["data"]["currentWorkspace"]["title"] == "두 번째 작업공간"
    assert len(created_payload["data"]["workspaces"]) == 2

    workspaces = created_payload["data"]["workspaces"]
    first_workspace_id = next(
        workspace["id"]
        for workspace in workspaces
        if workspace["title"] == "워크스페이스의 작업공간"
    )

    select_response = client.post(
        "/api/v1/auth/workspaces/select",
        json={"workspaceId": first_workspace_id},
    )

    assert select_response.status_code == 200
    assert select_response.json()["data"]["currentWorkspace"]["id"] == first_workspace_id


def test_read_auth_me_returns_current_workspace(client):
    ensure_response = client.post("/api/v1/auth/guest/ensure")

    me_response = client.get("/api/v1/auth/me")

    assert me_response.status_code == 200
    assert me_response.json()["data"]["currentWorkspace"]["id"] == ensure_response.json()["data"]["currentWorkspace"]["id"]


def test_read_workspace_activity_returns_recent_items(client):
    client.post("/api/v1/auth/guest/ensure")
    client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": "print(1)\n",
            "stdin": "",
            "visualizationMode": "none",
        },
    )
    client.post(
        "/api/v1/exams/submissions",
        json={
            "lessonId": "lesson-variable-flow",
            "sourceCode": "def transform_value(value):\n    return (value + 5) * 2\n",
        },
    )

    response = client.get("/api/v1/auth/activity")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert len(payload["data"]["recentExecutions"]) >= 1
    assert len(payload["data"]["recentExamAttempts"]) >= 1
