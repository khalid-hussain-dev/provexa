from __future__ import annotations

from fastapi.testclient import TestClient


def _login(client: TestClient) -> dict[str, str]:
    password = "StrongPassword123!"
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": "golden@example.com", "password": password, "name": "Golden Candidate"},
    )
    assert signup.status_code == 201, signup.text
    login = client.post(
        "/api/v1/auth/login", json={"email": "golden@example.com", "password": password}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_complete_local_golden_path(host_app) -> None:
    client = TestClient(host_app)
    headers = _login(client)

    candidate = client.put(
        "/api/v1/candidate",
        headers=headers,
        json={
            "name": "Golden Candidate",
            "headline": "Backend Engineer",
            "summary": "Builds evidence-backed backend services.",
            "preferences": {
                "target_role": "Backend Engineer",
                "experience_years": 3,
                "skills": ["Python", "FastAPI", "PostgreSQL"],
            },
        },
    )
    assert candidate.status_code == 200, candidate.text
    cv = client.post(
        "/api/v1/candidate/evidence",
        headers=headers,
        json={
            "source_type": "CV",
            "title": "Golden CV",
            "content": "Python backend engineer with FastAPI, PostgreSQL, pytest, and API delivery experience.",
        },
    )
    assert cv.status_code == 200, cv.text
    evidence_id = cv.json()["evidence_id"]

    profile = client.post("/api/v1/integration/profile/analyze", headers=headers)
    assert profile.status_code == 200, profile.text

    jobs = client.get("/api/v1/integration/platform/jobs", headers=headers)
    assert jobs.status_code == 200, jobs.text
    assert jobs.json()["jobs"]
    job_id = jobs.json()["jobs"][0]["job_id"]

    match = client.post(
        "/api/v1/integration/platform/match", headers=headers, json={"job_id": job_id}
    )
    assert match.status_code == 200, match.text
    assert 0 <= match.json()["match_score"] <= 100

    interview = client.post(
        "/api/v1/integration/interviews",
        headers=headers,
        json={"job_id": job_id, "num_questions": 2},
    )
    assert interview.status_code == 200, interview.text
    interview_payload = interview.json()
    first_answer = client.post(
        f"/api/v1/integration/interviews/{interview_payload['interview_id']}/answers",
        headers=headers,
        json={
            "question_id": interview_payload["first_question"]["question_id"],
            "answer": "I shipped a FastAPI service with measurable impact and ownership.",
        },
    )
    assert first_answer.status_code == 200, first_answer.text
    second_answer = client.post(
        f"/api/v1/integration/interviews/{interview_payload['interview_id']}/answers",
        headers=headers,
        json={
            "question_id": first_answer.json()["next_question"]["question_id"],
            "answer": "I used pytest and documented database and scalability trade-offs.",
        },
    )
    assert second_answer.status_code == 200, second_answer.text
    evaluation = client.post(
        f"/api/v1/integration/interviews/{interview_payload['interview_id']}/complete",
        headers=headers,
    )
    assert evaluation.status_code == 200, evaluation.text

    course = client.post(
        "/api/v1/integration/courses",
        headers=headers,
        json={"interview_id": interview_payload["interview_id"]},
    )
    assert course.status_code == 200, course.text
    course_payload = course.json()
    assert course_payload["modules"]
    progress = client.post(
        f"/api/v1/integration/courses/{course_payload['course_id']}/progress",
        headers=headers,
        json={"module_id": course_payload["modules"][0]["module_id"], "completion_percent": 100},
    )
    assert progress.status_code == 200, progress.text

    resume = client.post(
        "/api/v1/integration/resumes/optimize",
        headers=headers,
        json={"course_id": course_payload["course_id"], "evidence_id": evidence_id},
    )
    assert resume.status_code == 200, resume.text
    assert resume.json()["evidence_references"] == [evidence_id]

    from app.database.models import AnalysisRecord, CourseRecord, InterviewRecord, ResumeRecord
    from app.database.session import SessionLocal

    with SessionLocal() as session:
        assert session.query(AnalysisRecord).count() == 1
        assert session.query(InterviewRecord).count() == 1
        assert session.query(CourseRecord).count() == 1
        assert session.query(ResumeRecord).count() == 1
