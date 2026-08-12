from __future__ import annotations

from fastapi.testclient import TestClient


def _login(client: TestClient, email: str) -> dict[str, str]:
    password = "StrongPassword123!"
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "name": "Learning Candidate"},
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


def _prepare_candidate(client: TestClient, headers: dict[str, str]) -> str:
    updated = client.put(
        "/api/v1/candidate",
        headers=headers,
        json={
            "name": "Learning Candidate",
            "headline": "Backend Engineer",
            "preferences": {"target_role": "Backend Engineer", "skills": ["Python", "FastAPI"]},
        },
    )
    assert updated.status_code == 200, updated.text
    cv = client.post(
        "/api/v1/candidate/evidence",
        headers=headers,
        json={
            "source_type": "CV",
            "title": "Owned CV",
            "content": "Backend engineer with Python and FastAPI experience.",
        },
    )
    assert cv.status_code == 200, cv.text
    profile = client.post("/api/v1/integration/profile/analyze", headers=headers)
    assert profile.status_code == 200, profile.text
    return cv.json()["evidence_id"]


def _complete_interview(client: TestClient, headers: dict[str, str]) -> str:
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
            "answer": "I shipped a FastAPI service with measurable impact.",
        },
    )
    assert first.status_code == 200, first.text
    second = client.post(
        f"/api/v1/integration/interviews/{interview['interview_id']}/answers",
        headers=headers,
        json={
            "question_id": first.json()["next_question"]["question_id"],
            "answer": "I used pytest integration tests and documented trade-offs.",
        },
    )
    assert second.status_code == 200, second.text
    complete = client.post(
        f"/api/v1/integration/interviews/{interview['interview_id']}/complete",
        headers=headers,
    )
    assert complete.status_code == 200, complete.text
    return interview["interview_id"]


def test_course_adapter_consumes_interview_evaluation_and_preserves_progress(
    host_app, learning_gateway
) -> None:
    client = TestClient(host_app)
    headers = _login(client, "course@example.com")
    _prepare_candidate(client, headers)
    interview_id = _complete_interview(client, headers)

    course = client.post(
        "/api/v1/integration/courses",
        headers=headers,
        json={"interview_id": interview_id},
    )
    assert course.status_code == 200, course.text
    payload = course.json()
    assert payload["status"] == "GENERATED"
    assert len(payload["modules"]) == 2
    assert learning_gateway.course_inputs[-1]["current_score"] == 82

    progress = client.post(
        f"/api/v1/integration/courses/{payload['course_id']}/progress",
        headers=headers,
        json={"module_id": payload["modules"][0]["module_id"], "completion_percent": 50},
    )
    assert progress.status_code == 200, progress.text
    assert progress.json()["status"] == "updated"

    from app.database.models import CourseRecord, LearningProgressRecord
    from app.database.session import SessionLocal

    with SessionLocal() as session:
        stored = session.get(CourseRecord, payload["course_id"])
        progress_row = session.get(LearningProgressRecord, progress.json()["progress_id"])
        assert stored is not None
        assert stored.modules[0]["module_id"] == payload["modules"][0]["module_id"]
        assert progress_row is not None


def test_resume_adapter_requires_owned_cv_and_persists_evidence_locked_output(
    host_app, learning_gateway
) -> None:
    client = TestClient(host_app)
    headers = _login(client, "resume@example.com")
    evidence_id = _prepare_candidate(client, headers)
    interview_id = _complete_interview(client, headers)
    course = client.post(
        "/api/v1/integration/courses", headers=headers, json={"interview_id": interview_id}
    )
    assert course.status_code == 200, course.text

    response = client.post(
        "/api/v1/integration/resumes/optimize",
        headers=headers,
        json={"course_id": course.json()["course_id"], "evidence_id": evidence_id},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["result"]["injected_skills"] == ["Testing", "System Design"]
    assert "raw_provider_payload" not in payload["result"]
    assert payload["evidence_references"] == [evidence_id]
    assert learning_gateway.resume_inputs[-1]["resume_text"].startswith("Backend engineer")

    from app.database.models import ResumeRecord
    from app.database.session import SessionLocal

    with SessionLocal() as session:
        resume = session.get(ResumeRecord, payload["resume_id"])
        assert resume is not None
        assert resume.evidence_references == [evidence_id]
        assert "raw_provider_payload" not in resume.content


def test_learning_adapters_enforce_prerequisites_and_ownership(host_app) -> None:
    client = TestClient(host_app)
    headers = _login(client, "learning-owner@example.com")
    _prepare_candidate(client, headers)
    created = client.post(
        "/api/v1/integration/interviews", headers=headers, json={"job_id": _job_id()}
    )
    interview_id = created.json()["interview_id"]
    incomplete_course = client.post(
        "/api/v1/integration/courses", headers=headers, json={"interview_id": interview_id}
    )
    assert incomplete_course.status_code == 404

    other_headers = _login(client, "learning-other@example.com")
    blocked = client.post(
        "/api/v1/integration/courses", headers=other_headers, json={"interview_id": interview_id}
    )
    assert blocked.status_code == 404


def test_invalid_course_and_resume_outputs_are_rejected(host_app, learning_gateway) -> None:
    client = TestClient(host_app)
    headers = _login(client, "invalid-learning@example.com")
    evidence_id = _prepare_candidate(client, headers)
    interview_id = _complete_interview(client, headers)

    learning_gateway.course_result = {"unexpected": "invalid"}
    invalid_course = client.post(
        "/api/v1/integration/courses", headers=headers, json={"interview_id": interview_id}
    )
    assert invalid_course.status_code == 502
    assert invalid_course.json()["error"]["code"] == "INVALID_INTELLIGENCE_OUTPUT"

    learning_gateway.course_result = {
        "title": "Valid Course",
        "target_role": "Backend Engineer",
        "current_score": 82,
        "target_score": 97,
        "modules": [
            {
                "module_title": "Testing",
                "skill_name": "Testing",
                "concept_explanation": "Test concepts",
                "code_example": "pass",
                "validation_exercise": "Test",
            }
        ],
        "summary": "Valid summary",
    }
    valid_course = client.post(
        "/api/v1/integration/courses", headers=headers, json={"interview_id": interview_id}
    )
    assert valid_course.status_code == 200, valid_course.text
    learning_gateway.resume_result = {
        "original_resume_text": "tampered source",
        "updated_resume_text": "updated",
        "injected_skills": ["Testing"],
        "summary_of_changes": "changed",
    }
    invalid_resume = client.post(
        "/api/v1/integration/resumes/optimize",
        headers=headers,
        json={"course_id": valid_course.json()["course_id"], "evidence_id": evidence_id},
    )
    assert invalid_resume.status_code == 502
    assert invalid_resume.json()["error"]["code"] == "INVALID_INTELLIGENCE_OUTPUT"
