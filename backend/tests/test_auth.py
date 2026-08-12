from fastapi.testclient import TestClient

from app.auth.repository import reset_user_repository
from app.main import create_app


def _client() -> TestClient:
    reset_user_repository()
    return TestClient(create_app())


def test_signup_returns_user_and_access_token() -> None:
    client = _client()

    response = client.post("/api/v1/auth/signup", json={"email": "User@Example.com", "password": "strong-password"})

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "user@example.com"
    assert "password" not in body["user"]


def test_login_returns_access_token_for_valid_credentials() -> None:
    client = _client()
    client.post("/api/v1/auth/signup", json={"email": "user@example.com", "password": "strong-password"})

    response = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"})

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_invalid_login_uses_auth_error_envelope() -> None:
    client = _client()

    response = client.post("/api/v1/auth/login", json={"email": "missing@example.com", "password": "wrong"})

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "AUTHENTICATION_ERROR",
            "message": "Invalid email or password",
            "details": {},
        }
    }


def test_duplicate_signup_uses_conflict_error_envelope() -> None:
    client = _client()
    payload = {"email": "user@example.com", "password": "strong-password"}
    client.post("/api/v1/auth/signup", json=payload)

    response = client.post("/api/v1/auth/signup", json=payload)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_current_user_requires_and_accepts_bearer_token() -> None:
    client = _client()
    signup = client.post("/api/v1/auth/signup", json={"email": "user@example.com", "password": "strong-password"})
    token = signup.json()["access_token"]

    missing = client.get("/api/v1/auth/me")
    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == "AUTHENTICATION_ERROR"

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_current_user_rejects_invalid_bearer_token() -> None:
    client = _client()

    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-valid-token"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"
