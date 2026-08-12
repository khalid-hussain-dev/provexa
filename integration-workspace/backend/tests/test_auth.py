from fastapi.testclient import TestClient

from app.auth.repository import SqlAlchemyUserRepository, reset_user_repository
from app.auth.two_factor import generate_totp_code
from app.database.session import SessionLocal
from app.main import create_app


def _client() -> TestClient:
    reset_user_repository()
    return TestClient(create_app())


def test_signup_returns_contract_response() -> None:
    client = _client()

    response = client.post("/api/v1/auth/signup", json={"name": "Khalid", "email": "User@Example.com", "password": "strong-password"})

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"user_id", "requires_2fa_setup"}
    assert body["user_id"]
    assert body["requires_2fa_setup"] is False


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
    client.post("/api/v1/auth/signup", json={"email": "user@example.com", "password": "strong-password"})
    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"})
    token = login.json()["access_token"]

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


def test_logout_revokes_current_token() -> None:
    client = _client()
    client.post("/api/v1/auth/signup", json={"email": "user@example.com", "password": "strong-password"})
    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"})
    token = login.json()["access_token"]

    logout = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout.status_code == 200
    assert logout.json() == {"status": "logged_out"}

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


def test_forgot_and_reset_password_flow() -> None:
    client = _client()
    client.post("/api/v1/auth/signup", json={"email": "user@example.com", "password": "old-password"})

    forgot = client.post("/api/v1/auth/forgot-password", json={"email": "user@example.com"})
    assert forgot.status_code == 200
    reset_token = forgot.json()["reset_token"]
    assert reset_token

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "new-password"},
    )
    assert reset.status_code == 200
    assert reset.json() == {"status": "password_reset"}

    old_login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "old-password"})
    assert old_login.status_code == 401

    new_login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "new-password"})
    assert new_login.status_code == 200
    assert new_login.json()["access_token"]


def test_forgot_password_does_not_disclose_missing_accounts() -> None:
    client = _client()

    response = client.post("/api/v1/auth/forgot-password", json={"email": "missing@example.com"})

    assert response.status_code == 200
    assert response.json() == {"status": "accepted", "reset_token": None}


def test_two_factor_setup_and_login_verification_flow() -> None:
    client = _client()
    client.post("/api/v1/auth/signup", json={"email": "user@example.com", "password": "strong-password"})
    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"})
    token = login.json()["access_token"]

    setup = client.post("/api/v1/auth/2fa/setup", headers={"Authorization": f"Bearer {token}"})
    assert setup.status_code == 200
    secret = setup.json()["secret"]
    assert setup.json()["provisioning_uri"].startswith("otpauth://totp/PROVEXA:")

    verify_setup = client.post(
        "/api/v1/auth/2fa/verify",
        json={"code": generate_totp_code(secret)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert verify_setup.status_code == 200
    assert verify_setup.json()["authenticated"] is True
    assert verify_setup.json()["access_token"]

    pending_login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"})
    assert pending_login.status_code == 200
    assert pending_login.json()["requires_2fa"] is True

    pending_token = pending_login.json()["access_token"]
    blocked = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {pending_token}"})
    assert blocked.status_code == 401

    final = client.post(
        "/api/v1/auth/2fa/verify",
        json={"code": generate_totp_code(secret)},
        headers={"Authorization": f"Bearer {pending_token}"},
    )
    assert final.status_code == 200
    assert final.json()["access_token"]
    assert final.json()["authenticated"] is True


def test_two_factor_rejects_invalid_code() -> None:
    client = _client()
    client.post("/api/v1/auth/signup", json={"email": "user@example.com", "password": "strong-password"})
    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"})
    token = login.json()["access_token"]
    setup = client.post("/api/v1/auth/2fa/setup", headers={"Authorization": f"Bearer {token}"})

    with SessionLocal() as session:
        assert SqlAlchemyUserRepository(session).get_by_email("user@example.com") is not None
    valid_code = generate_totp_code(setup.json()["secret"])
    invalid_code = "000000" if valid_code != "000000" else "111111"
    response = client.post(
        "/api/v1/auth/2fa/verify",
        json={"code": invalid_code},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"
