from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database.session import get_db_session
from app.core.errors import NotFoundError
from app.jobs.repository import JobRepository
from app.jobs.schemas import (
    JobDetailResponse,
    JobListResponse,
    JobRecommendationResponse,
    JobRecommendRequest,
    JobRecommendResponse,
    JobRequirementResponse,
    JobSummaryResponse,
)
from app.jobs.service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    source: str | None = None,
    query: str | None = None,
    location: str | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> JobListResponse:
    jobs, total = JobService(session).list_jobs(page=page, limit=limit, source=source, query=query, location=location)
    return JobListResponse(
        jobs=[
            JobSummaryResponse(
                job_id=UUID(str(job.id)),
                title=job.title,
                company=job.company,
                location=job.location,
                source=job.source,
            )
            for job in jobs
        ],
        page=page,
        limit=limit,
        total=total,
    )


@router.get("/{job_id:uuid}", response_model=JobDetailResponse)
def get_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> JobDetailResponse:
    service = JobService(session)
    job = service.get_job(str(job_id))
    if not job:
        raise NotFoundError("Job not found", {"job_id": str(job_id)})
    return _job_detail_response(job, JobRepository(session).get_requirements(str(job.id)))


@router.post("/recommend", response_model=JobRecommendResponse)
def recommend_jobs(
    payload: JobRecommendRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> JobRecommendResponse:
    recommendations = JobService(session).recommend_jobs(current_user, limit=payload.limit, location=payload.location)
    return JobRecommendResponse(
        jobs=[
            JobRecommendationResponse(
                job_id=UUID(str(item.job.id)),
                title=item.job.title,
                company=item.job.company,
                match_score=item.match_score,
                readiness_score=item.readiness_score,
                source=item.job.source,
            )
            for item in recommendations
        ]
    )


def _job_detail_response(job, requirements) -> JobDetailResponse:
    return JobDetailResponse(
        job_id=UUID(str(job.id)),
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        seniority=job.seniority,
        source=job.source,
        source_url=job.source_url,
        responsibilities=job.responsibilities or [],
        metadata=job.metadata_json or {},
        requirements=[
            JobRequirementResponse(
                id=UUID(str(requirement.id)),
                skill_name=requirement.skill_name,
                importance=round(requirement.importance),
                requirement_type=requirement.requirement_type,
                evidence_expectation=requirement.evidence_expectation,
            )
            for requirement in requirements
        ],
    )
