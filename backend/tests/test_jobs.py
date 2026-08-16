from fastapi.testclient import TestClient

from app.auth.repository import reset_user_repository
from app.main import create_app
from app.jobs.repository import _adzuna_search_variants


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
            "content": "Built FastAPI APIs with PostgreSQL, Redis, Docker, and pytest.",
            "external_url": None,
        },
        headers=headers,
    )


def test_jobs_list_returns_seeded_demo_jobs() -> None:
    client = _client()
    headers = _headers(client)

    response = client.get("/api/v1/jobs", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 3
    assert body["jobs"]


def test_jobs_list_falls_back_when_query_is_too_narrow() -> None:
    client = _client()
    headers = _headers(client)

    response = client.get("/api/v1/jobs?query=DefinitelyNoMatch", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["jobs"]


def test_job_detail_returns_requirements() -> None:
    client = _client()
    headers = _headers(client)
    jobs = client.get("/api/v1/jobs", headers=headers).json()["jobs"]
    job_id = jobs[0]["job_id"]

    response = client.get(f"/api/v1/jobs/{job_id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == job_id
    assert body["requirements"]


def test_jobs_recommendation_is_ranked_from_candidate_evidence() -> None:
    client = _client()
    headers = _headers(client)
    _seed_candidate(client, headers)

    response = client.post("/api/v1/jobs/recommend", json={"limit": 2, "location": "Remote"}, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["jobs"]
    assert body["jobs"][0]["title"] == "Backend Developer"
    if len(body["jobs"]) > 1:
        assert body["jobs"][0]["match_score"] >= body["jobs"][1]["match_score"]


def test_jobs_detail_rejects_unknown_id() -> None:
    client = _client()
    headers = _headers(client)

    response = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000", headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_adzuna_search_variants_expand_mobile_roles() -> None:
    variants = _adzuna_search_variants(query="Mobile Engineer", location="Karachi, Pakistan")

    assert variants[0] == ("Mobile Engineer", "Karachi, Pakistan")
    assert ("Mobile Engineer", None) in variants
    assert ("Mobile Developer", "Karachi, Pakistan") in variants
    assert ("Android Developer", None) in variants
