from __future__ import annotations

from fastapi.testclient import TestClient


def _signup_and_login(client: TestClient, email: str) -> dict[str, str]:
    password = "StrongPassword123!"
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "name": "Test Candidate"},
    )
    assert signup.status_code == 201, signup.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_profile_analysis_maps_owned_evidence_and_persists_snapshot(host_app, profile_gateway) -> None:
    client = TestClient(host_app)
    headers = _signup_and_login(client, "candidate@example.com")

    candidate = client.put(
        "/api/v1/candidate",
        headers=headers,
        json={
            "name": "Candidate One",
            "headline": "Backend Engineer",
            "summary": "Builds reliable APIs.",
            "preferences": {
                "target_role": "Backend Engineer",
                "experience_years": 3,
                "skills": ["Python", "FastAPI"],
            },
        },
    )
    assert candidate.status_code == 200, candidate.text
    candidate_id = candidate.json()["id"]

    cv = client.post(
        "/api/v1/candidate/evidence",
        headers=headers,
        json={
            "source_type": "CV",
            "title": "Resume",
            "content": "Python backend engineer with FastAPI experience.",
        },
    )
    github = client.post(
        "/api/v1/candidate/evidence",
        headers=headers,
        json={
            "source_type": "GITHUB",
            "title": "GitHub",
            "external_url": "https://github.com/example",
        },
    )
    assert cv.status_code == 200, cv.text
    assert github.status_code == 200, github.text

    response = client.post("/api/v1/integration/profile/analyze", headers=headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "completed"
    assert len(payload["source_evidence_ids"]) == 2
    assert payload["profile_context"]["primary_domain"] == "Backend Engineering"
    assert "raw_result" not in payload["profile_context"]

    mapped = profile_gateway.inputs[-1]
    assert mapped.email == "candidate@example.com"
    assert mapped.target_role == "Backend Engineer"
    assert mapped.experience_years == 3
    assert "FastAPI experience" in mapped.resume_text
    assert mapped.github_url == "https://github.com/example"

    from app.database.session import SessionLocal
    from integration.profile_persistence import ProfileAnalysisSnapshotRecord

    with SessionLocal() as session:
        snapshot = session.get(ProfileAnalysisSnapshotRecord, payload["analysis_id"])
        assert snapshot is not None
        assert snapshot.candidate_id == candidate_id
        assert snapshot.source_evidence_ids == [cv.json()["evidence_id"], github.json()["evidence_id"]]
        assert "raw_result" not in snapshot.profile_context


def test_profile_analysis_requires_authentication(host_app) -> None:
    response = TestClient(host_app).post("/api/v1/integration/profile/analyze")
    assert response.status_code == 401


def test_profile_analysis_cannot_read_another_users_evidence(host_app, profile_gateway) -> None:
    client = TestClient(host_app)
    first_headers = _signup_and_login(client, "first@example.com")
    evidence = client.post(
        "/api/v1/candidate/evidence",
        headers=first_headers,
        json={"source_type": "CV", "title": "Private", "content": "Private resume"},
    )
    assert evidence.status_code == 200, evidence.text

    second_headers = _signup_and_login(client, "second@example.com")
    response = client.post("/api/v1/integration/profile/analyze", headers=second_headers)
    assert response.status_code == 200, response.text
    assert response.json()["source_evidence_ids"] == []
    assert profile_gateway.inputs[-1].email == "second@example.com"
    assert profile_gateway.inputs[-1].resume_text is None


def test_invalid_intelligence_output_is_rejected_and_not_persisted(host_app, profile_gateway) -> None:
    client = TestClient(host_app)
    headers = _signup_and_login(client, "invalid@example.com")
    profile_gateway.result = {"unexpected": "unusable"}

    response = client.post("/api/v1/integration/profile/analyze", headers=headers)
    assert response.status_code == 502, response.text
    assert response.json()["error"]["code"] == "INVALID_INTELLIGENCE_OUTPUT"

    from app.database.session import SessionLocal
    from integration.profile_persistence import ProfileAnalysisSnapshotRecord
    from sqlalchemy import select

    with SessionLocal() as session:
        assert session.scalar(select(ProfileAnalysisSnapshotRecord)) is None
