from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.candidates.repository import CandidateRepository
from app.core.errors import NotFoundError
from app.database.models import CourseRecord, InterviewRecord
from app.database.session import get_db_session
from app.courses.schemas import CourseDetailResponse, CourseGenerateRequest, CourseGenerateResponse, CourseModuleResponse, CourseProgressRequest
from app.courses.service import CourseService
from app.jobs.repository import JobRepository

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("/generate", response_model=CourseGenerateResponse)
def generate_course(
    payload: CourseGenerateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> CourseGenerateResponse:
    candidate = CandidateRepository(session).get_or_create_for_user(current_user)
    job = JobRepository(session).get_job(str(payload.job_id))
    if job is None:
        raise NotFoundError("Job not found", {"job_id": str(payload.job_id)})
    interview_record = session.get(InterviewRecord, str(payload.interview_id))
    if interview_record is None:
        raise NotFoundError("Interview not found", {"interview_id": str(payload.interview_id)})
    if interview_record.candidate_id != str(candidate.id):
        raise NotFoundError("Interview not found", {"interview_id": str(payload.interview_id)})
    course, modules = CourseService(session).generate_course(str(candidate.id), job, interview_record)
    return CourseGenerateResponse(
        course_id=UUID(str(course.id)),
        title=course.title,
        estimated_duration=course.estimated_duration,
        modules=[_module_response(module) for module in modules],
    )


@router.get("/{course_id}", response_model=CourseDetailResponse)
def get_course(
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> CourseDetailResponse:
    candidate = CandidateRepository(session).get_or_create_for_user(current_user)
    course = CourseService(session).get_course(str(course_id))
    if course is None:
        raise NotFoundError("Course not found", {"course_id": str(course_id)})
    if course.candidate_id != str(candidate.id):
        raise NotFoundError("Course not found", {"course_id": str(course_id)})
    return CourseDetailResponse(
        course_id=UUID(str(course.id)),
        status=course.status,
        title=course.title,
        objective=course.objective,
        estimated_duration=course.estimated_duration,
        modules=[_module_response(module) for module in course.module_rows],
        progress=[
            {
                "module_id": UUID(str(progress.module_id)),
                "completion_percent": progress.completion_percent,
                "assessment_score": progress.assessment_score,
            }
            for progress in course.progress_entries
        ],
    )


@router.post("/{course_id}/progress")
def update_progress(
    course_id: UUID,
    payload: CourseProgressRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> dict:
    candidate = CandidateRepository(session).get_or_create_for_user(current_user)
    course = session.get(CourseRecord, str(course_id))
    if course is None or course.candidate_id != str(candidate.id):
        raise NotFoundError("Course not found", {"course_id": str(course_id)})
    progress = CourseService(session).update_progress(str(course_id), str(payload.module_id), payload.completion_percent, payload.assessment_score)
    return {
        "progress_id": UUID(str(progress.id)),
        "status": "updated",
    }


def _module_response(module) -> CourseModuleResponse:
    return CourseModuleResponse(
        module_id=UUID(str(module.id)),
        sequence=module.sequence,
        title=module.title,
        objective=module.objective,
        content=module.content or {},
        challenge=module.challenge or {},
    )
