from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.candidates.repository import CandidateRepository
from app.core.errors import NotFoundError
from app.database.models import InterviewQuestionRecord, InterviewRecord
from app.database.session import get_db_session
from app.interviews.schemas import InterviewAnswerRequest, InterviewAnswerResponse, InterviewCompleteResponse, InterviewCreateRequest, InterviewCreateResponse, InterviewQuestionResponse
from app.interviews.service import InterviewService
from app.jobs.repository import JobRepository

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("", response_model=InterviewCreateResponse)
def create_interview(
    payload: InterviewCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> InterviewCreateResponse:
    candidate = CandidateRepository(session).get_or_create_for_user(current_user)
    job = JobRepository(session).get_job(str(payload.job_id))
    if job is None:
        raise NotFoundError("Job not found", {"job_id": str(payload.job_id)})
    interview, first_question = InterviewService(session).create_interview(str(candidate.id), job)
    return InterviewCreateResponse(
        interview_id=UUID(str(interview.id)),
        first_question=_question_response(first_question),
    )


@router.post("/{interview_id}/answer", response_model=InterviewAnswerResponse)
def answer_interview_question(
    interview_id: UUID,
    payload: InterviewAnswerRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> InterviewAnswerResponse:
    candidate = CandidateRepository(session).get_or_create_for_user(current_user)
    interview_service = InterviewService(session)
    interview = session.get(InterviewRecord, str(interview_id))
    if interview is None or interview.candidate_id != str(candidate.id):
        raise NotFoundError("Interview not found", {"interview_id": str(interview_id)})
    answer, next_question = interview_service.answer_question(str(interview_id), str(payload.question_id), payload.answer)
    return InterviewAnswerResponse(
        score=round(answer.score or 0),
        feedback=answer.feedback or "",
        next_question=_question_response(next_question) if next_question else None,
    )


@router.post("/{interview_id}/complete", response_model=InterviewCompleteResponse)
def complete_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> InterviewCompleteResponse:
    candidate = CandidateRepository(session).get_or_create_for_user(current_user)
    interview = session.get(InterviewRecord, str(interview_id))
    if interview is None or interview.candidate_id != str(candidate.id):
        raise NotFoundError("Interview not found", {"interview_id": str(interview_id)})
    result = InterviewService(session).complete_interview(str(interview_id))
    return InterviewCompleteResponse(**result)


def _question_response(question: InterviewQuestionRecord | None) -> InterviewQuestionResponse | None:
    if question is None:
        return None
    return InterviewQuestionResponse(
        question_id=UUID(str(question.id)),
        question=question.question,
        competency=question.competency,
    )
