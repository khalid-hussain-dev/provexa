from fastapi.testclient import TestClient

from app.auth.repository import get_user_repository, reset_user_repository
from app.auth.two_factor import generate_totp_code
from app.main import create_app


def _client() -> TestClient:
    reset_user_repository()
    return TestClient(create_app())


def _signup_and_login(client: TestClient) -> str:
    client.post("/api/v1/auth/signup", json={"name": "Khalid", "email": "user@example.com", "password": "strong-password"})
    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_signup_matches_public_contract_shape() -> None:
    client = _client()

    response = client.post("/api/v1/auth/signup", json={"name": "Khalid", "email": "User@Example.com", "password": "strong-password"})

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"user_id", "requires_2fa_setup"}
    assert body["requires_2fa_setup"] is False


def test_login_matches_public_contract_shape_without_2fa() -> None:
    client = _client()
    client.post("/api/v1/auth/signup", json={"name": "Khalid", "email": "user@example.com", "password": "strong-password"})

    response = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["requires_2fa"] is False


def test_forgot_password_is_simulated_and_does_not_disclose_accounts() -> None:
    client = _client()

    response = client.post("/api/v1/auth/forgot-password", json={"email": "missing@example.com"})

    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}


def test_two_factor_setup_and_login_verification_flow() -> None:
    client = _client()
    token = _signup_and_login(client)

    setup = client.post("/api/v1/auth/2fa/setup", headers={"Authorization": f"Bearer {token}"})
    assert setup.status_code == 200
    secret = setup.json()["secret"]

    repository = get_user_repository()
    user = repository.get_by_email("user@example.com")
    assert user is not None
    AuthCode = generate_totp_code(secret)
    verify = client.post(
        "/api/v1/auth/2fa/verify",
        json={"code": AuthCode},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert verify.status_code == 401

    pending_login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"})
    assert pending_login.status_code == 200
    assert pending_login.json()["requires_2fa"] is True

    final = client.post(
        "/api/v1/auth/2fa/verify",
        json={"code": generate_totp_code(secret)},
        headers={"Authorization": f"Bearer {pending_login.json()['access_token']}"},
    )
    assert final.status_code == 200
    assert final.json()["authenticated"] is True
    assert final.json()["access_token"]


def test_pending_two_factor_token_cannot_access_protected_routes() -> None:
    client = _client()
    token = _signup_and_login(client)
    setup = client.post("/api/v1/auth/2fa/setup", headers={"Authorization": f"Bearer {token}"})
    secret = setup.json()["secret"]

    user = get_user_repository().get_by_email("user@example.com")
    assert user is not None
    user.two_factor_enabled = True
    user.two_factor_secret = secret

    pending_login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"})
    pending_token = pending_login.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {pending_token}"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"
