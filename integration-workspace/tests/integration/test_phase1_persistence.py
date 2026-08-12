from fastapi.testclient import TestClient

from app.database.models import CandidateRecord, EvidenceRecord, UserRecord
from app.database.session import SessionLocal


def _login(client: TestClient, email: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/signup",
        json={"name": email.split("@", 1)[0], "email": email, "password": "strong-password"},
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strong-password"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_user_profile_and_evidence_are_persisted_and_owned(host_app) -> None:
    client = TestClient(host_app)
    first_headers = _login(client, "first@example.com")
    second_headers = _login(client, "second@example.com")

    first_profile = client.put(
        "/api/v1/candidate",
        headers=first_headers,
        json={"name": "First", "headline": "Engineer", "summary": "Private profile"},
    )
    evidence = client.post(
        "/api/v1/candidate/evidence",
        headers=first_headers,
        json={"source_type": "CV", "title": "Private CV", "content": "Python evidence"},
    )

    second_profile = client.get("/api/v1/candidate", headers=second_headers)

    assert first_profile.status_code == 200
    assert evidence.status_code == 200
    assert second_profile.status_code == 200
    assert second_profile.json()["name"] != "First"

    with SessionLocal() as session:
        users = session.query(UserRecord).order_by(UserRecord.email).all()
        candidates = session.query(CandidateRecord).all()
        evidence_rows = session.query(EvidenceRecord).all()

    assert {user.email for user in users} == {"first@example.com", "second@example.com"}
    assert len(candidates) == 2
    assert len(evidence_rows) == 1
    assert evidence_rows[0].candidate_id == next(
        candidate.id for candidate in candidates if candidate.name == "First"
    )


def test_postgresql_is_required_outside_explicit_test_mode(monkeypatch) -> None:
    from integration.errors import DependencyUnavailableError
    from integration.runtime import validate_database_configuration

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///not-allowed.db")
    try:
        validate_database_configuration()
    except DependencyUnavailableError as exc:
        assert "PostgreSQL" in exc.message
    else:
        raise AssertionError("SQLite must not be accepted as the production persistence authority")

