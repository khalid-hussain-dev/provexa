from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.analysis.service import AnalysisService
from app.auth.models import User
from app.candidates.repository import CandidateRepository
from app.database.session import get_db_session
from app.jobs.service import JobService

from .security import get_current_user


class JobSelectionResponse(BaseModel):
    job_id: UUID
    title: str
    company: str
    location: str | None = None
    source: str
    description: str | None = None
    source_url: str | None = None


class JobSelectionListResponse(BaseModel):
    jobs: list[JobSelectionResponse]
    page: int
    limit: int
    total: int


class MatchRequest(BaseModel):
    job_id: UUID


class MatchResponse(BaseModel):
    analysis_id: UUID
    match_score: int
    readiness_score: int
    strengths: list[dict] = []
    gaps: list[dict] = []
    recommendations: list = []
    evidence_summary: list = []


def build_platform_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/integration/platform", tags=["integration-platform"])

    @router.get("/jobs", response_model=JobSelectionListResponse)
    def list_jobs(
        page: int = Query(default=1, ge=1),
        limit: int = Query(default=10, ge=1, le=50),
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> JobSelectionListResponse:
        candidate = CandidateRepository(session).get_or_create_for_user(current_user)
        preferences = candidate.preferences or {}
        target_query = preferences.get("target_role") or candidate.headline or None
        jobs, total = JobService(session).list_jobs(
            page=page, limit=limit, source=None, query=target_query, location=candidate.location
        )
        return JobSelectionListResponse(
            jobs=[
                JobSelectionResponse(
                    job_id=UUID(str(job.id)),
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    source=job.source,
                    description=job.description,
                    source_url=job.source_url,
                )
                for job in jobs
            ],
            page=page,
            limit=limit,
            total=total,
        )

    @router.post("/match", response_model=MatchResponse)
    def match_candidate(
        payload: MatchRequest,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> MatchResponse:
        candidate = CandidateRepository(session).get_or_create_for_user(current_user)
        result = AnalysisService(session).match_candidate_to_job(candidate, str(payload.job_id))
        return MatchResponse(**result)

    return router
