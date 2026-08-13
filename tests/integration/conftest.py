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
def interview_gateway():
    class FakeInterviewGateway:
        def __init__(self) -> None:
            self.generation_inputs = []
            self.evaluation_inputs = []
            self.question_result = [
                {"question": "Explain a FastAPI service you shipped.", "category": "FastAPI", "difficulty": "medium"},
                {"question": "How did you test the service?", "category": "Testing", "difficulty": "medium"},
            ]
            self.evaluation_result = {
                "candidate_name": "Test Candidate",
                "target_role": "Backend Engineer",
                "overall_score": 82,
                "assessed_level": "mid",
                "skill_assessments": [
                    {"skill_name": "FastAPI", "percentage": 84, "strength_level": "advanced", "evidence": ["answer-1"]}
                ],
                "analysis": {
                    "strengths": ["API design"],
                    "weaknesses": ["Testing depth"],
                    "improvement_areas": ["Add integration-test examples"],
                },
                "course_recommendations": [],
                "interview_summary": "A solid backend interview with clear API reasoning.",
                "role_match_percentage": 80,
                "raw_provider_payload": "must not persist",
            }

        async def generate_questions(self, profile_context, num_questions):
            self.generation_inputs.append((profile_context, num_questions))
            return self.question_result[:num_questions]

        async def evaluate(self, profile_context, questions, responses):
            self.evaluation_inputs.append((profile_context, questions, responses))
            return self.evaluation_result

    return FakeInterviewGateway()


@pytest.fixture
def learning_gateway():
    class FakeLearningGateway:
        def __init__(self) -> None:
            self.course_inputs = []
            self.resume_inputs = []
            self.course_result = {
                "title": "Backend Readiness Sprint",
                "target_role": "Backend Engineer",
                "current_score": 82,
                "target_score": 97,
                "selected_priority_skills": ["Testing", "System Design"],
                "modules": [
                    {
                        "module_title": "Testing Foundations",
                        "skill_name": "Testing",
                        "concept_explanation": "Build reliable integration tests.",
                        "code_example": "def test_api(): pass",
                        "validation_exercise": "Write an ownership test.",
                        "solution_hint": "Use an isolated database.",
                    },
                    {
                        "module_title": "System Design",
                        "skill_name": "System Design",
                        "concept_explanation": "Design service boundaries and trade-offs.",
                        "code_example": "class Service: pass",
                        "validation_exercise": "Describe a scalable API.",
                        "solution_hint": "Start with the data flow.",
                    },
                ],
                "summary": "A focused course for the identified interview gaps.",
                "raw_provider_payload": "must not persist",
            }
            self.resume_result = None

        async def generate_course(self, **kwargs):
            self.course_inputs.append(kwargs)
            return self.course_result

        async def optimize_resume(self, **kwargs):
            self.resume_inputs.append(kwargs)
            return self.resume_result or {
                "original_resume_text": kwargs["resume_text"],
                "updated_resume_text": kwargs["resume_text"] + "\nSkills: Testing, System Design",
                "injected_skills": list(kwargs["newly_learned_skills"]),
                "summary_of_changes": "Added course skills to the skills section.",
                "raw_provider_payload": "must not persist",
            }

    return FakeLearningGateway()


@pytest.fixture
def host_app(intelligence_app: FastAPI, profile_gateway, interview_gateway, learning_gateway) -> FastAPI:
    from integration.host import create_host_app
    from integration.session_store import InMemorySessionStore

    return create_host_app(
        intelligence_app,
        session_store=InMemorySessionStore(),
        profile_gateway=profile_gateway,
        interview_gateway=interview_gateway,
        learning_gateway=learning_gateway,
    )


@pytest.fixture(autouse=True)
def reset_database() -> None:
    from app.auth.repository import reset_user_repository
    from integration.interview_persistence import reset_interview_integration_records
    from integration.learning_persistence import reset_learning_integration_records
    from integration.profile_persistence import reset_profile_analysis_snapshots

    reset_learning_integration_records()
    reset_interview_integration_records()
    reset_profile_analysis_snapshots()
    reset_user_repository()
