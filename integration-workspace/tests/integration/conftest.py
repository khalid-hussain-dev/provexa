from __future__ import annotations

import os
import secrets
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI

WORKSPACE = Path(__file__).resolve().parents[2]
BACKEND = WORKSPACE / "backend"
for path in (WORKSPACE, BACKEND):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = str(
    Path(tempfile.gettempdir()) / f"provexa_phase1_{os.getpid()}_{secrets.token_hex(4)}.db"
).replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{os.environ['DATABASE_URL']}"
os.environ["INTEGRATION_ALLOW_SQLITE_TESTS"] = "true"
os.environ["JWT_SECRET"] = secrets.token_urlsafe(32)


@pytest.fixture
def intelligence_app() -> FastAPI:
    app = FastAPI(title="Fake Intelligence Host")

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"status": "healthy", "service": "AI Interview & Assessment System", "version": "1.0.0"}

    @app.post("/api/v1/profile/analyze")
    async def profile_analyze() -> dict[str, str]:
        return {"status": "success"}

    @app.post("/api/v1/interview/questions")
    async def interview_questions() -> dict[str, str]:
        return {"status": "success"}

    @app.post("/api/v1/interview/evaluate")
    async def interview_evaluate() -> dict[str, str]:
        return {"status": "success"}

    @app.post("/api/v1/jobs/recommend")
    async def jobs_recommend() -> dict[str, str]:
        return {"status": "success"}

    @app.post("/api/v1/assessment/complete")
    async def assessment_complete() -> dict[str, str]:
        return {"status": "success"}

    @app.post("/api/v1/course/generate")
    async def course_generate() -> dict[str, str]:
        return {"status": "success"}

    @app.post("/api/v1/resume/inject-skills")
    async def resume_inject() -> dict[str, str]:
        return {"status": "success"}

    return app


@pytest.fixture
def profile_gateway():
    class FakeProfileGateway:
        def __init__(self) -> None:
            self.inputs = []
            self.result = {
                "candidate_summary": "Validated profile summary",
                "primary_domain": "Backend Engineering",
                "secondary_domains": ["Platform Engineering"],
                "domain_confidence": 88,
                "all_skills": ["Python", "FastAPI", "PostgreSQL"],
                "skill_clusters": {"backend": ["Python", "FastAPI"]},
                "technical_strengths": ["API design"],
                "potential_weaknesses": ["Kubernetes"],
                "interview_readiness": "medium",
                "recommended_interview_depth": "intermediate",
                "profile_context": "Evidence-backed test context",
                "raw_result": "must not be persisted",
            }

        async def analyze(self, candidate):
            self.inputs.append(candidate)
            return self.result

    return FakeProfileGateway()


@pytest.fixture
def host_app(intelligence_app: FastAPI, profile_gateway) -> FastAPI:
    from integration.host import create_host_app
    from integration.session_store import InMemorySessionStore

    return create_host_app(
        intelligence_app,
        session_store=InMemorySessionStore(),
        profile_gateway=profile_gateway,
    )


@pytest.fixture(autouse=True)
def reset_database() -> None:
    from app.auth.repository import reset_user_repository
    from integration.profile_persistence import reset_profile_analysis_snapshots

    reset_user_repository()
    reset_profile_analysis_snapshots()
