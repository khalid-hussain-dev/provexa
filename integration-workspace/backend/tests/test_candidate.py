from fastapi.testclient import TestClient

from app.auth.repository import reset_user_repository
from app.main import create_app


def _client() -> TestClient:
    reset_user_repository()
    return TestClient(create_app())


def _auth_headers(client: TestClient) -> dict[str, str]:
    client.post("/api/v1/auth/signup", json={"name": "Khalid", "email": "user@example.com", "password": "strong-password"})
    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_candidate_requires_authentication() -> None:
    client = _client()

    response = client.get("/api/v1/candidate")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


def test_get_candidate_creates_default_profile_for_user() -> None:
    client = _client()
    headers = _auth_headers(client)

    response = client.get("/api/v1/candidate", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"]
    assert body["name"] == "Khalid"
    assert body["preferences"] == {}


def test_update_candidate_profile() -> None:
    client = _client()
    headers = _auth_headers(client)

    response = client.put(
        "/api/v1/candidate",
        json={
            "headline": "Backend Developer",
            "summary": "Python and APIs",
            "location": "Lahore",
            "preferences": {"remote": True},
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["headline"] == "Backend Developer"
    assert body["summary"] == "Python and APIs"
    assert body["location"] == "Lahore"
    assert body["preferences"] == {"remote": True}


def test_create_candidate_evidence() -> None:
    client = _client()
    headers = _auth_headers(client)

    response = client.post(
        "/api/v1/candidate/evidence",
        json={
            "source_type": "CV",
            "title": "Khalid Resume",
            "content": "Built FastAPI systems",
            "external_url": None,
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["evidence_id"]
    assert response.json()["status"] == "stored"


def test_evidence_rejects_unknown_source_type() -> None:
    client = _client()
    headers = _auth_headers(client)

    response = client.post(
        "/api/v1/candidate/evidence",
        json={"source_type": "ALIEN", "title": "Unknown", "content": "x"},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
