def test_register_user_returns_authenticated_session(client):
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
    assert payload["data"]["user"]["email"] == "tester@example.com"
    assert "codeviz_session" in response.cookies


def test_login_user_returns_authenticated_session(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "strongpass123",
            "name": "로그인테스터",
        },
    )

    client.post("/api/v1/auth/logout")

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "strongpass123",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["isAuthenticated"] is True
    assert payload["data"]["user"]["name"] == "로그인테스터"


def test_read_auth_me_returns_null_without_session(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["data"] is None


def test_logout_clears_session(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "logout@example.com",
            "password": "strongpass123",
            "name": "로그아웃테스터",
        },
    )

    logout_response = client.post("/api/v1/auth/logout")
    me_response = client.get("/api/v1/auth/me")

    assert logout_response.status_code == 200
    assert me_response.status_code == 200
    assert me_response.json()["data"] is None


def test_learning_categories_requires_login(client):
    response = client.get("/api/v1/learning/categories")

    assert response.status_code == 401
    assert response.json()["detail"] == "로그인이 필요합니다."
