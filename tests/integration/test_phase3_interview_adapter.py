from __future__ import annotations

from fastapi.testclient import TestClient


def _login(client: TestClient, email: str) -> dict[str, str]:
    password = "StrongPassword123!"
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "name": "Interview Candidate"},
    )
    assert signup.status_code == 201, signup.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _job_id() -> str:
    from app.database.session import SessionLocal
    from app.jobs.repository import JobRepository

    with SessionLocal() as session:
        jobs, _ = JobRepository(session).list_jobs(page=1, limit=1)
        return str(jobs[0].id)


def _prepare_profile(client: TestClient, headers: dict[str, str], profile_gateway) -> None:
    update = client.put(
        "/api/v1/candidate",
        headers=headers,
        json={
            "name": "Interview Candidate",
            "headline": "Backend Engineer",
            "preferences": {"target_role": "Backend Engineer", "skills": ["Python", "FastAPI"]},
        },
    )
    assert update.status_code == 200, update.text
    profile = client.post("/api/v1/integration/profile/analyze", headers=headers)
    assert profile.status_code == 200, profile.text


def test_interview_adapter_generates_questions_from_profile_and_job(
    host_app, profile_gateway, interview_gateway
) -> None:
    client = TestClient(host_app)
    headers = _login(client, "interview@example.com")
    _prepare_profile(client, headers, profile_gateway)

    response = client.post(
        "/api/v1/integration/interviews",
        headers=headers,
        json={"job_id": _job_id(), "num_questions": 2},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "CREATED"
    assert payload["total_questions"] == 2
    assert payload["first_question"]["question_id"]
    assert interview_gateway.generation_inputs[-1][0]["target_job"]["title"] in {
        "Backend Developer",
        "Full Stack Engineer",
        "Platform Engineer",
    }

    from app.database.models import InterviewQuestionRecord, InterviewRecord
    from app.database.session import SessionLocal

    with SessionLocal() as session:
        interview = session.get(InterviewRecord, payload["interview_id"])
        questions = list(
            session.query(InterviewQuestionRecord)
            .filter(InterviewQuestionRecord.interview_id == payload["interview_id"])
            .all()
        )
        assert interview is not None
        assert interview.status == "CREATED"
        assert len(questions) == 2


def test_interview_adapter_persists_transcript_and_uses_intelligence_evaluation(
    host_app, profile_gateway, interview_gateway
) -> None:
    client = TestClient(host_app)
    headers = _login(client, "evaluation@example.com")
    _prepare_profile(client, headers, profile_gateway)
    created = client.post(
        "/api/v1/integration/interviews",
        headers=headers,
        json={"job_id": _job_id(), "num_questions": 2},
    )
    assert created.status_code == 200, created.text
    interview = created.json()

    first = client.post(
        f"/api/v1/integration/interviews/{interview['interview_id']}/answers",
        headers=headers,
        json={
            "question_id": interview["first_question"]["question_id"],
            "answer": "I shipped a FastAPI service with ownership and measurable impact.",
            "confidence": 8,
        },
    )
    assert first.status_code == 200, first.text
    second_question = first.json()["next_question"]
    assert second_question is not None
    second = client.post(
        f"/api/v1/integration/interviews/{interview['interview_id']}/answers",
        headers=headers,
        json={
            "question_id": second_question["question_id"],
            "answer": "I added pytest integration testing and explained the trade-offs.",
        },
    )
    assert second.status_code == 200, second.text

    complete = client.post(
        f"/api/v1/integration/interviews/{interview['interview_id']}/complete",
        headers=headers,
    )
    assert complete.status_code == 200, complete.text
    result = complete.json()
    assert result["status"] == "COMPLETED"
    assert result["result"]["overall_score"] == 82
    assert "raw_provider_payload" not in result["result"]
    assert len(interview_gateway.evaluation_inputs[-1][2]) == 2

    from app.database.models import InterviewRecord
    from app.database.session import SessionLocal
    from integration.interview_persistence import InterviewEvaluationRecord

    with SessionLocal() as session:
        record = session.get(InterviewRecord, interview["interview_id"])
        evaluation = session.get(InterviewEvaluationRecord, result["evaluation_id"])
        assert record.status == "COMPLETED"
        assert record.overall_score == 82
        assert evaluation is not None
        assert "raw_provider_payload" not in evaluation.result


def test_interview_adapter_enforces_ownership_and_completion_boundary(
    host_app, profile_gateway
) -> None:
    client = TestClient(host_app)
    owner_headers = _login(client, "owner@example.com")
    _prepare_profile(client, owner_headers, profile_gateway)
    created = client.post(
        "/api/v1/integration/interviews",
        headers=owner_headers,
        json={"job_id": _job_id(), "num_questions": 2},
    )
    interview_id = created.json()["interview_id"]

    incomplete = client.post(
        f"/api/v1/integration/interviews/{interview_id}/complete",
        headers=owner_headers,
    )
    assert incomplete.status_code == 409
    assert incomplete.json()["error"]["code"] == "INCOMPLETE_INTERVIEW"

    other_headers = _login(client, "other@example.com")
    blocked = client.post(
        f"/api/v1/integration/interviews/{interview_id}/complete",
        headers=other_headers,
    )
    assert blocked.status_code == 404


def test_invalid_intelligence_interview_output_is_not_persisted(
    host_app, profile_gateway, interview_gateway
) -> None:
    client = TestClient(host_app)
    headers = _login(client, "bad-output@example.com")
    _prepare_profile(client, headers, profile_gateway)
    interview_gateway.question_result = [{"unexpected": "invalid"}]

    response = client.post(
        "/api/v1/integration/interviews",
        headers=headers,
        json={"job_id": _job_id(), "num_questions": 1},
    )
    assert response.status_code == 502, response.text
    assert response.json()["error"]["code"] == "INVALID_INTELLIGENCE_OUTPUT"

    from app.database.models import InterviewRecord
    from app.database.session import SessionLocal
    from sqlalchemy import select

    with SessionLocal() as session:
        assert session.scalar(select(InterviewRecord)) is None
