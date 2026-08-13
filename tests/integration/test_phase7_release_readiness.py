from __future__ import annotations


def test_release_readiness_passes_in_test_mode_without_secret_values(host_app, monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("INTEGRATION_ALLOW_SQLITE_TESTS", "true")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    from fastapi.testclient import TestClient

    response = TestClient(host_app).get("/api/v1/readiness/release")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["manifest"]["status"] == "passed"
    assert payload["manifest"]["checked_files"] == 92
    assert payload["blockers"] == []
    assert "GEMINI_API_KEY" not in response.text


def test_release_readiness_blocks_production_test_fallbacks(host_app, monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("INTEGRATION_ALLOW_SQLITE_TESTS", "true")
    monkeypatch.setenv("INTEGRATION_ALLOW_INMEMORY_SESSIONS", "true")

    from integration.release_readiness import evaluate_release_readiness

    result = evaluate_release_readiness()
    assert result["status"] == "blocked"
    assert len(result["production_flag_violations"]) == 2


def test_original_intelligence_routes_are_preserved(host_app) -> None:
    original_paths = {
        "/",
        "/api/v1/profile/analyze",
        "/api/v1/interview/questions",
        "/api/v1/interview/evaluate",
        "/api/v1/jobs/recommend",
        "/api/v1/assessment/complete",
        "/api/v1/course/generate",
        "/api/v1/resume/inject-skills",
    }
    route_paths = set(host_app.openapi()["paths"])
    assert original_paths.issubset(route_paths)
    assert "/api/v1/integration/profile/analyze" in route_paths
    assert "/api/v1/integration/interviews" in route_paths
    assert "/api/v1/integration/courses" in route_paths
    assert "/api/v1/integration/resumes/optimize" in route_paths
