from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.models import User
from app.candidates.repository import CandidateRepository
from app.database.session import get_db_session

from .profile_adapter import (
    CandidateProfileAnalysisAdapter,
    ProfileAnalysisGateway,
    ProfileAnalysisResponse,
)
from .security import get_current_user


def build_profile_router(gateway: ProfileAnalysisGateway) -> APIRouter:
    router = APIRouter(prefix="/api/v1/integration/profile", tags=["integration-profile"])

    @router.post("/analyze", response_model=ProfileAnalysisResponse)
    async def analyze_profile(
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> ProfileAnalysisResponse:
        candidate = CandidateRepository(session).get_or_create_for_user(current_user)
        return await CandidateProfileAnalysisAdapter(gateway).analyze_and_persist(
            user=current_user,
            candidate=candidate,
            session=session,
        )

    return router
