from fastapi.testclient import TestClient

from app.auth.repository import reset_user_repository
from app.main import create_app


def _client() -> TestClient:
    reset_user_repository()
    return TestClient(create_app())


def _headers(client: TestClient) -> dict[str, str]:
    client.post("/api/v1/auth/signup", json={"name": "Khalid", "email": "user@example.com", "password": "strong-password"})
    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _seed_candidate(client: TestClient, headers: dict[str, str]) -> None:
    client.post(
        "/api/v1/candidate/evidence",
        json={
            "source_type": "CV",
            "title": "Backend Experience",
            "content": "Built FastAPI APIs with PostgreSQL, Redis, and Docker. Tested with pytest.",
            "external_url": None,
        },
        headers=headers,
    )


def test_candidate_analysis_returns_capabilities() -> None:
    client = _client()
    headers = _headers(client)
    _seed_candidate(client, headers)

    response = client.post("/api/v1/analysis/candidate", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["analysis_id"]
    assert body["capabilities"]


def test_job_analysis_returns_requirements() -> None:
    client = _client()
    headers = _headers(client)

    response = client.post(
        "/api/v1/analysis/job",
        json={
            "job_description": "FastAPI backend role using PostgreSQL, Redis, Docker, and pytest.",
            "title": "Backend Developer",
            "company": "Example Inc",
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"]
    assert body["requirements"]


def test_match_analysis_returns_readiness_and_gaps() -> None:
    client = _client()
    headers = _headers(client)
    _seed_candidate(client, headers)

    job = client.post(
        "/api/v1/analysis/job",
        json={
            "job_description": "FastAPI backend role using PostgreSQL, Redis, Docker, and pytest.",
            "title": "Backend Developer",
            "company": "Example Inc",
        },
        headers=headers,
    ).json()

    response = client.post("/api/v1/analysis/match", json={"job_id": job["job_id"]}, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"]
    assert 0 <= body["match_score"] <= 100
    assert 0 <= body["readiness_score"] <= 100
    assert isinstance(body["strengths"], list)
    assert isinstance(body["gaps"], list)


def test_match_rejects_unknown_job() -> None:
    client = _client()
    headers = _headers(client)

    response = client.post("/api/v1/analysis/match", json={"job_id": "00000000-0000-0000-0000-000000000000"}, headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
