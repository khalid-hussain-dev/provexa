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


def _seed_candidate_with_evidence(client: TestClient, headers: dict[str, str]) -> None:
    client.post(
        "/api/v1/candidate/evidence",
        json={
            "source_type": "CV",
            "title": "Backend Experience",
            "content": "Built FastAPI APIs with PostgreSQL, Redis, Docker, pytest, and interview-ready delivery notes.",
            "external_url": None,
        },
        headers=headers,
    )


def _create_job_and_interview(client: TestClient, headers: dict[str, str]) -> tuple[dict, dict]:
    job = client.post(
        "/api/v1/analysis/job",
        json={
            "job_description": "FastAPI backend role using PostgreSQL, Redis, Docker, and pytest.",
            "title": "Backend Developer",
            "company": "Example Inc",
        },
        headers=headers,
    ).json()
    interview = client.post("/api/v1/interviews", json={"job_id": job["job_id"]}, headers=headers)
    assert interview.status_code == 200
    return job, interview.json()


def test_interview_flow_returns_scores_and_completion_summary() -> None:
    client = _client()
    headers = _auth_headers(client)
    _seed_candidate_with_evidence(client, headers)
    _, interview = _create_job_and_interview(client, headers)

    first_question = interview["first_question"]
    answer = client.post(
        f"/api/v1/interviews/{interview['interview_id']}/answer",
        json={
            "question_id": first_question["question_id"],
            "answer": "I shipped a FastAPI feature using PostgreSQL and Docker. The trade-off was simpler scaling first, then optimizing later.",
        },
        headers=headers,
    )

    assert answer.status_code == 200
    assert answer.json()["score"] >= 50
    assert answer.json()["next_question"]

    complete = client.post(f"/api/v1/interviews/{interview['interview_id']}/complete", headers=headers)
    assert complete.status_code == 200
    body = complete.json()
    assert 0 <= body["overall_score"] <= 100
    assert body["verdict"] in {"APPLY", "APPLY_WITH_CAUTION", "NOT_READY"}
    assert isinstance(body["strengths"], list)
    assert isinstance(body["recommendations"], list)


def test_course_generation_and_progress_updates() -> None:
    client = _client()
    headers = _auth_headers(client)
    _seed_candidate_with_evidence(client, headers)
    job = client.post(
        "/api/v1/analysis/job",
        json={
            "job_description": "FastAPI backend role using PostgreSQL, Redis, Docker, and pytest.",
            "title": "Backend Developer",
            "company": "Example Inc",
        },
        headers=headers,
    ).json()
    interview = client.post("/api/v1/interviews", json={"job_id": job["job_id"]}, headers=headers).json()

    course = client.post(
        "/api/v1/courses/generate",
        json={"job_id": job["job_id"], "interview_id": interview["interview_id"]},
        headers=headers,
    )
    assert course.status_code == 200
    course_body = course.json()
    assert course_body["modules"]

    detail = client.get(f"/api/v1/courses/{course_body['course_id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["status"] in {"GENERATED", "IN_PROGRESS", "COMPLETED"}

    module_id = course_body["modules"][0]["module_id"]
    progress = client.post(
        f"/api/v1/courses/{course_body['course_id']}/progress",
        json={"module_id": module_id, "completion_percent": 75, "assessment_score": 88},
        headers=headers,
    )
    assert progress.status_code == 200
    assert progress.json()["status"] == "updated"


def test_resume_templates_generation_and_subscription_demo() -> None:
    client = _client()
    headers = _auth_headers(client)
    _seed_candidate_with_evidence(client, headers)
    job, interview = _create_job_and_interview(client, headers)

    templates = client.get("/api/v1/resumes/templates")
    assert templates.status_code == 200
    assert templates.json()["templates"][0]["id"] == "minimal"

    resume = client.post(
        "/api/v1/resumes/generate",
        json={"job_id": job["job_id"], "template": "minimal"},
        headers=headers,
    )
    assert resume.status_code == 200
    assert resume.json()["content"]["header"]["name"] == "Khalid"

    checkout = client.post("/api/v1/subscription/checkout", json={"plan": "pro"}, headers=headers)
    assert checkout.status_code == 200
    checkout_id = checkout.json()["checkout_id"]

    confirm = client.post("/api/v1/subscription/confirm", json={"checkout_id": checkout_id}, headers=headers)
    assert confirm.status_code == 200
    assert confirm.json() == {"status": "ACTIVE", "demo_payment": True}
