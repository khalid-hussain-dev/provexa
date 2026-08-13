from __future__ import annotations


def test_provider_readiness_is_configuration_only_and_never_exposes_values(host_app, monkeypatch) -> None:
    secret_values = {
        "GEMINI_API_KEY": "gemini-secret-value",
        "GROQ_API_KEY": "groq-secret-value",
        "GITHUB_TOKEN": "github-secret-value",
        "JOB_API_KEY": "adzuna-secret-value",
        "ADZUNA_APP_ID": "adzuna-app-secret-value",
    }
    for name, value in secret_values.items():
        monkeypatch.setenv(name, value)

    from fastapi.testclient import TestClient

    response = TestClient(host_app).get("/api/v1/readiness/providers")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["checks"] == "configuration_only"
    assert payload["live_provider_calls"] is False
    assert all(payload["providers"][name]["configured"] for name in ("gemini", "groq", "github", "adzuna"))
    serialized = response.text
    for value in secret_values.values():
        assert value not in serialized


def test_provider_readiness_reports_degraded_ai_without_keys(host_app, monkeypatch) -> None:
    for name in ("GEMINI_API_KEY", "GROQ_API_KEY", "GITHUB_TOKEN", "JOB_API_KEY", "ADZUNA_APP_ID"):
        monkeypatch.delenv(name, raising=False)

    from fastapi.testclient import TestClient

    response = TestClient(host_app).get("/api/v1/readiness/providers")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["providers"]["gemini"]["configured"] is False
    assert payload["providers"]["groq"]["configured"] is False
    assert payload["fallbacks"]["candidate_job_match"] == "platform_deterministic"
    assert payload["fallbacks"]["job_selection"] == "platform_seeded_or_persisted"
