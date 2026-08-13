from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.models import User
from app.candidates.repository import CandidateRepository
from app.core.errors import NotFoundError
from app.database.models import InterviewRecord
from app.database.session import get_db_session
from app.jobs.repository import JobRepository

from .interview_adapter import (
    InterviewAdapter,
    InterviewAnalysisGateway,
    InterviewAnswerAcceptedResponse,
    InterviewCreateResponse,
    InterviewEvaluationResponse,
)
from .security import get_current_user


class InterviewCreateRequest(BaseModel):
    job_id: UUID
    num_questions: int = Field(default=5, ge=1, le=20)


class InterviewAnswerRequest(BaseModel):
    question_id: UUID
    answer: str = Field(min_length=1, max_length=10000)
    confidence: int = Field(default=5, ge=1, le=10)


def build_interview_router(gateway: InterviewAnalysisGateway) -> APIRouter:
    router = APIRouter(prefix="/api/v1/integration/interviews", tags=["integration-interviews"])

    @router.post("", response_model=InterviewCreateResponse)
    async def create_interview(
        payload: InterviewCreateRequest,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> InterviewCreateResponse:
        candidate = CandidateRepository(session).get_or_create_for_user(current_user)
        job = JobRepository(session).get_job(str(payload.job_id))
        if job is None:
            raise NotFoundError("Job not found", {"job_id": str(payload.job_id)})
        return await InterviewAdapter(gateway).create(
            user=current_user,
            candidate=candidate,
            job=job,
            num_questions=payload.num_questions,
            session=session,
        )

    @router.post("/{interview_id}/answers", response_model=InterviewAnswerAcceptedResponse)
    def answer_interview(
        interview_id: UUID,
        payload: InterviewAnswerRequest,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> InterviewAnswerAcceptedResponse:
        interview = _owned_interview(session, str(interview_id), current_user)
        return InterviewAdapter(gateway).record_answer(
            interview=interview,
            question_id=str(payload.question_id),
            answer=payload.answer,
            confidence=payload.confidence,
            session=session,
        )

    @router.post("/{interview_id}/complete", response_model=InterviewEvaluationResponse)
    async def complete_interview(
        interview_id: UUID,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> InterviewEvaluationResponse:
        interview = _owned_interview(session, str(interview_id), current_user)
        return await InterviewAdapter(gateway).complete(interview=interview, session=session)

    return router


def _owned_interview(session: Session, interview_id: str, user: User) -> InterviewRecord:
    candidate = CandidateRepository(session).get_or_create_for_user(user)
    interview = session.get(InterviewRecord, interview_id)
    if interview is None or interview.candidate_id != str(candidate.id):
        raise NotFoundError("Interview not found", {"interview_id": interview_id})
    return interview
