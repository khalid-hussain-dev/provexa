from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .errors import DependencyUnavailableError
from .runtime import validate_database_configuration, validate_security_configuration
from .session_store import SessionStore, build_session_store


def create_host_app(
    intelligence_app: FastAPI,
    *,
    session_store: SessionStore | None = None,
    profile_gateway=None,
    interview_gateway=None,
) -> FastAPI:
    """Decorate the unchanged Intelligence app with Phase 1 Platform services."""

    validate_database_configuration()
    validate_security_configuration()
    from .auth_router import router as auth_router
    from .candidate_router import router as candidate_router
    from .interview_adapter import IntelligenceInterviewGateway
    from .interview_persistence import InterviewContextRecord, InterviewEvaluationRecord  # noqa: F401
    from .interview_router import build_interview_router
    from .profile_adapter import IntelligenceProfileGateway
    from .profile_persistence import ProfileAnalysisSnapshotRecord  # noqa: F401
    from .profile_router import build_profile_router
    from app.core.errors import AppError, error_envelope
    from app.database.session import SessionLocal, init_database

    store = session_store or build_session_store()
    init_database()

    intelligence_app.state.integration_session_store = store
    intelligence_app.state.integration_persistence_authority = "postgresql"
    intelligence_app.include_router(auth_router)
    intelligence_app.include_router(candidate_router)
    intelligence_app.include_router(build_profile_router(profile_gateway or IntelligenceProfileGateway()))
    intelligence_app.include_router(
        build_interview_router(interview_gateway or IntelligenceInterviewGateway())
    )

    @intelligence_app.get("/api/v1/readiness", tags=["integration-support"])
    async def readiness() -> dict:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        if not store.ping():
            raise DependencyUnavailableError("Redis session store is not ready")
        return {
            "status": "ready",
            "persistence": "postgresql",
            "session_store": store.mode,
            "intelligence_host": "active",
        }

    @intelligence_app.exception_handler(AppError)
    async def integration_app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(exc.code, exc.message, exc.details),
        )

    return intelligence_app
