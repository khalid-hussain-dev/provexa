from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analysis.schemas import CandidateAnalysisResponse, JobAnalysisRequest, JobAnalysisResponse, MatchRequest, MatchResponse
from app.analysis.service import AnalysisService
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.candidates.repository import CandidateRepository
from app.database.session import get_db_session

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/candidate", response_model=CandidateAnalysisResponse)
def analyze_candidate(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> CandidateAnalysisResponse:
    candidate = CandidateRepository(session).get_or_create_for_user(current_user)
    analysis_id, capabilities = AnalysisService(session).analyze_candidate(candidate)
    return CandidateAnalysisResponse(analysis_id=UUID(analysis_id), capabilities=capabilities)


@router.post("/job", response_model=JobAnalysisResponse)
def analyze_job(
    payload: JobAnalysisRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> JobAnalysisResponse:
    job, requirements = AnalysisService(session).analyze_job(payload.model_dump())
    return JobAnalysisResponse(job_id=UUID(str(job.id)), requirements=requirements)


@router.post("/match", response_model=MatchResponse)
def match_candidate(
    payload: MatchRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> MatchResponse:
    candidate = CandidateRepository(session).get_or_create_for_user(current_user)
    result = AnalysisService(session).match_candidate_to_job(candidate, str(payload.job_id))
    return MatchResponse(**result)
