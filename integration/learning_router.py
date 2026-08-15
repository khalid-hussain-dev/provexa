from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.models import User
from app.database.session import get_db_session

from .learning_adapter import (
    CourseProgressResponse,
    CourseResponse,
    IntelligenceLearningGateway,
    LearningAdapter,
    LearningGateway,
    ResumeOptimizationResponse,
)
from .security import get_current_user


class CourseGenerateRequest(BaseModel):
    interview_id: UUID


class CourseProgressRequest(BaseModel):
    module_id: UUID
    completion_percent: float = Field(ge=0, le=100)
    assessment_score: float | None = Field(default=None, ge=0, le=100)


class ResumeOptimizeRequest(BaseModel):
    course_id: UUID
    evidence_id: UUID


def build_learning_router(gateway: LearningGateway) -> APIRouter:
    router = APIRouter(prefix="/api/v1/integration", tags=["integration-learning"])

    @router.post("/courses", response_model=CourseResponse)
    async def generate_course(
        payload: CourseGenerateRequest,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> CourseResponse:
        return await LearningAdapter(gateway).generate_course(
            user=current_user, interview_id=str(payload.interview_id), session=session
        )

    @router.post("/courses/{course_id}/progress", response_model=CourseProgressResponse)
    def update_course_progress(
        course_id: UUID,
        payload: CourseProgressRequest,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> CourseProgressResponse:
        return LearningAdapter(gateway).update_progress(
            user=current_user,
            course_id=str(course_id),
            module_id=str(payload.module_id),
            completion_percent=payload.completion_percent,
            assessment_score=payload.assessment_score,
            session=session,
        )

    @router.post("/resumes/optimize", response_model=ResumeOptimizationResponse)
    async def optimize_resume(
        payload: ResumeOptimizeRequest,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> ResumeOptimizationResponse:
        return await LearningAdapter(gateway).optimize_resume(
            user=current_user,
            course_id=str(payload.course_id),
            evidence_id=str(payload.evidence_id),
            session=session,
        )

    return router
