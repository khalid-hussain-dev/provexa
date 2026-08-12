from fastapi.testclient import TestClient


def _signup_and_login(client: TestClient, email: str) -> str:
    signup = client.post(
        "/api/v1/auth/signup",
        json={"name": email.split("@", 1)[0], "email": email, "password": "strong-password"},
    )
    assert signup.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strong-password"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def test_authentication_is_available_through_intelligence_host(host_app) -> None:
    client = TestClient(host_app)
    token = _signup_and_login(client, "user@example.com")

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_password_validation_and_duplicate_signup_use_platform_contracts(host_app) -> None:
    client = TestClient(host_app)
    weak = client.post(
        "/api/v1/auth/signup",
        json={"email": "user@example.com", "password": "short"},
    )
    assert weak.status_code == 422

    _signup_and_login(client, "user@example.com")
    duplicate = client.post(
        "/api/v1/auth/signup",
        json={"email": "user@example.com", "password": "strong-password"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CONFLICT"

    invalid = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )
    assert invalid.status_code == 401
    assert invalid.json()["error"]["code"] == "AUTHENTICATION_ERROR"


def test_logout_revokes_redis_session_and_blocks_access(host_app) -> None:
    client = TestClient(host_app)
    token = _signup_and_login(client, "user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    logout = client.post("/api/v1/auth/logout", headers=headers)
    blocked = client.get("/api/v1/auth/me", headers=headers)

    assert logout.status_code == 200
    assert blocked.status_code == 401
    assert blocked.json()["error"]["code"] == "AUTHENTICATION_ERROR"


def test_unprotected_and_intelligence_routes_remain_separate(host_app) -> None:
    client = TestClient(host_app)

    assert client.get("/").status_code == 200
    assert client.post("/api/v1/profile/analyze").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401

