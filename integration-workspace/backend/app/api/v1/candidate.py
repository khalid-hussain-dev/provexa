from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.candidates.repository import CandidateRepository
from app.candidates.schemas import CandidateResponse, CandidateUpdateRequest, EvidenceCreateRequest, EvidenceStoredResponse
from app.database.models import CandidateRecord
from app.database.session import get_db_session

router = APIRouter(prefix="/candidate", tags=["candidate"])


@router.get("", response_model=CandidateResponse)
def get_candidate(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> CandidateResponse:
    candidate = CandidateRepository(session).get_or_create_for_user(current_user)
    return _candidate_response(candidate)


@router.put("", response_model=CandidateResponse)
def update_candidate(
    payload: CandidateUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> CandidateResponse:
    candidate = CandidateRepository(session).update_for_user(
        current_user,
        name=payload.name,
        headline=payload.headline,
        summary=payload.summary,
        location=payload.location,
        preferences=payload.preferences,
    )
    return _candidate_response(candidate)


@router.post("/evidence", response_model=EvidenceStoredResponse)
def create_evidence(
    payload: EvidenceCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> EvidenceStoredResponse:
    repository = CandidateRepository(session)
    candidate = repository.get_or_create_for_user(current_user)
    evidence = repository.create_evidence(
        candidate.id,
        source_type=payload.source_type,
        title=payload.title,
        content=payload.content,
        external_url=payload.external_url,
        metadata=payload.metadata,
    )
    return EvidenceStoredResponse(evidence_id=UUID(str(evidence.id)))


def _candidate_response(candidate: CandidateRecord) -> CandidateResponse:
    return CandidateResponse(
        id=UUID(str(candidate.id)),
        name=candidate.name or "",
        headline=candidate.headline,
        summary=candidate.summary,
        location=candidate.location,
        preferences=candidate.preferences or {},
    )
