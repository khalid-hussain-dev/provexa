from __future__ import annotations

import os
from typing import Any


def provider_status() -> dict[str, Any]:
    """Return configuration state only; never contact providers or expose secrets."""

    gemini = _configured("GEMINI_API_KEY")
    groq = _configured("GROQ_API_KEY")
    github = _configured("GITHUB_TOKEN")
    adzuna = _configured("JOB_API_KEY") and _configured("ADZUNA_APP_ID")
    ai_configured = gemini or groq
    return {
        "status": "ready" if ai_configured else "degraded",
        "checks": "configuration_only",
        "live_provider_calls": False,
        "providers": {
            "gemini": {"configured": gemini, "role": "primary"},
            "groq": {"configured": groq, "role": "fallback"},
            "github": {"configured": github, "role": "profile_enrichment"},
            "adzuna": {"configured": adzuna, "role": "external_job_source"},
        },
        "fallbacks": {
            "candidate_job_match": "platform_deterministic",
            "job_selection": "platform_seeded_or_persisted",
            "intelligence_question_generation": "intelligence_internal_fallback_when_available",
            "intelligence_course_generation": "intelligence_internal_fallback_when_available",
            "intelligence_resume_optimization": "intelligence_internal_fallback_when_available",
        },
    }


def _configured(name: str) -> bool:
    value = os.getenv(name, "").strip()
    return bool(value) and not value.lower().startswith(("your_", "replace_", "changeme"))
