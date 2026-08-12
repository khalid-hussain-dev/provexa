from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.candidates.repository import CandidateRepository
from app.core.errors import NotFoundError
from app.database.session import get_db_session
from app.jobs.repository import JobRepository
from app.resumes.schemas import ResumeGenerateRequest, ResumeGenerateResponse, ResumeTemplateResponse, ResumeTemplatesResponse
from app.resumes.service import ResumeService
from app.resumes.service import TEMPLATES

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.get("/templates", response_model=ResumeTemplatesResponse)
def list_templates() -> ResumeTemplatesResponse:
    return ResumeTemplatesResponse(templates=[ResumeTemplateResponse.model_validate(template) for template in TEMPLATES])


@router.post("/generate", response_model=ResumeGenerateResponse)
def generate_resume(
    payload: ResumeGenerateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ResumeGenerateResponse:
    candidate = CandidateRepository(session).get_or_create_for_user(current_user)
    job = JobRepository(session).get_job(str(payload.job_id))
    if job is None:
        raise NotFoundError("Job not found", {"job_id": str(payload.job_id)})
    resume = ResumeService(session).generate_resume(candidate, job, payload.template)
    return ResumeGenerateResponse(
        resume_id=UUID(str(resume.id)),
        version=resume.version,
        content=resume.content,
        evidence_references=resume.evidence_references,
    )
