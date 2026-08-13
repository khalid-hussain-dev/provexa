from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.candidates.repository import CandidateRepository
from app.core.errors import NotFoundError
from app.database.models import (
    CandidateRecord,
    CourseModuleRecord,
    CourseRecord,
    EvidenceRecord,
    InterviewRecord,
    ResumeRecord,
)
from app.courses.service import CourseService

from .errors import InvalidIntelligenceOutputError
from .interview_adapter import NormalizedInterviewResult
from .interview_persistence import InterviewIntegrationRepository
from .learning_persistence import LearningIntegrationRepository


class NormalizedCourseModule(BaseModel):
    model_config = ConfigDict(extra="ignore")

    module_title: str = Field(min_length=1, max_length=255)
    skill_name: str = Field(min_length=1, max_length=120)
    concept_explanation: str = Field(min_length=1, max_length=20000)
    code_example: str = Field(min_length=1, max_length=20000)
    validation_exercise: str = Field(min_length=1, max_length=10000)
    solution_hint: str | None = Field(default=None, max_length=10000)


class NormalizedCourse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1, max_length=255)
    target_role: str = Field(min_length=1, max_length=255)
    current_score: float = Field(ge=0, le=100)
    target_score: float = Field(ge=0, le=100)
    selected_priority_skills: list[str] = Field(default_factory=list)
    modules: list[NormalizedCourseModule] = Field(min_length=1, max_length=10)
    summary: str = Field(min_length=1, max_length=20000)


class NormalizedResumeOptimization(BaseModel):
    model_config = ConfigDict(extra="ignore")

    original_resume_text: str = Field(min_length=1, max_length=100000)
    updated_resume_text: str = Field(min_length=1, max_length=100000)
    injected_skills: list[str] = Field(default_factory=list)
    summary_of_changes: str = Field(min_length=1, max_length=10000)

    @model_validator(mode="after")
    def require_changed_text(self) -> "NormalizedResumeOptimization":
        if not self.updated_resume_text.strip():
            raise ValueError("updated resume is empty")
        return self


class CourseResponse(BaseModel):
    course_id: UUID
    status: str = "GENERATED"
    title: str
    target_role: str
    current_score: float
    target_score: float
    modules: list[dict] = Field(default_factory=list)


class CourseProgressResponse(BaseModel):
    progress_id: UUID
    status: str = "updated"


class ResumeOptimizationResponse(BaseModel):
    resume_id: UUID
    version: int
    evidence_references: list[UUID] = Field(default_factory=list)
    result: NormalizedResumeOptimization


class LearningGateway(Protocol):
    async def generate_course(
        self,
        *,
        target_role: str,
        current_score: float,
        weaknesses: Sequence[str],
        improvement_areas: Sequence[str],
    ) -> Mapping[str, Any]: ...

    async def optimize_resume(
        self, *, resume_text: str, newly_learned_skills: Sequence[str]
    ) -> Mapping[str, Any]: ...


class IntelligenceLearningGateway:
    """Lazy bridge to unchanged Intelligence course and resume methods."""

    def __init__(self, intelligence_system: Any | None = None) -> None:
        self._intelligence_system = intelligence_system

    def _system(self) -> Any:
        if self._intelligence_system is None:
            from interview_system import InterviewSystem

            self._intelligence_system = InterviewSystem()
        return self._intelligence_system

    async def generate_course(self, **kwargs: Any) -> Mapping[str, Any]:
        result = await self._system().generate_targeted_course(**kwargs)
        return result.model_dump() if hasattr(result, "model_dump") else result

    async def optimize_resume(self, **kwargs: Any) -> Mapping[str, Any]:
        result = await self._system().optimize_resume(**kwargs)
        return result.model_dump() if hasattr(result, "model_dump") else result


class LearningAdapter:
    def __init__(self, gateway: LearningGateway) -> None:
        self._gateway = gateway

    async def generate_course(
        self,
        *,
        user: User,
        interview_id: str,
        session: Session,
    ) -> CourseResponse:
        candidate = CandidateRepository(session).get_or_create_for_user(user)
        interview = session.get(InterviewRecord, interview_id)
        if interview is None or interview.candidate_id != str(candidate.id):
            raise NotFoundError("Interview not found", {"interview_id": interview_id})
        evaluation = InterviewIntegrationRepository(session).get_evaluation(interview_id)
        if evaluation is None:
            raise NotFoundError("Complete the interview before generating a course", {"interview_id": interview_id})
        result = _validate_interview_result(evaluation.result)
        job = interview.job
        raw_course = await self._gateway.generate_course(
            target_role=result.target_role or job.title,
            current_score=result.overall_score,
            weaknesses=result.analysis.weaknesses,
            improvement_areas=_string_items(result.analysis.improvement_areas),
        )
        course = _validate_course(raw_course)

        course_record = CourseRecord(
            id=str(uuid4()),
            candidate_id=str(candidate.id),
            job_id=str(job.id),
            title=course.title,
            objective=course.summary,
            estimated_duration=f"{len(course.modules)} modules",
            status="GENERATED",
            modules=[],
        )
        session.add(course_record)
        session.flush()
        module_rows: list[CourseModuleRecord] = []
        module_payloads: list[dict] = []
        for sequence, module in enumerate(course.modules, start=1):
            row = CourseModuleRecord(
                id=str(uuid4()),
                course_id=course_record.id,
                sequence=sequence,
                title=module.module_title,
                objective=module.concept_explanation,
                content={
                    "skill_name": module.skill_name,
                    "concept_explanation": module.concept_explanation,
                    "code_example": module.code_example,
                    "solution_hint": module.solution_hint,
                },
                challenge={"validation_exercise": module.validation_exercise},
            )
            session.add(row)
            session.flush()
            module_rows.append(row)
            module_payloads.append(
                {
                    "module_id": row.id,
                    "sequence": sequence,
                    "title": row.title,
                    "objective": row.objective,
                    "content": row.content,
                    "challenge": row.challenge,
                }
            )
        course_record.modules = module_payloads
        LearningIntegrationRepository(session).create_course_context(
            course_id=course_record.id,
            interview_id=interview_id,
            evaluation_id=evaluation.id,
        )
        session.commit()
        return CourseResponse(
            course_id=UUID(course_record.id),
            title=course_record.title,
            target_role=course.target_role,
            current_score=course.current_score,
            target_score=course.target_score,
            modules=module_payloads,
        )

    def update_progress(
        self,
        *,
        user: User,
        course_id: str,
        module_id: str,
        completion_percent: float,
        assessment_score: float | None,
        session: Session,
    ) -> CourseProgressResponse:
        candidate = CandidateRepository(session).get_or_create_for_user(user)
        course = session.get(CourseRecord, course_id)
        if course is None or course.candidate_id != str(candidate.id):
            raise NotFoundError("Course not found", {"course_id": course_id})
        progress = CourseService(session).update_progress(
            course_id, module_id, completion_percent, assessment_score
        )
        return CourseProgressResponse(progress_id=UUID(progress.id))

    async def optimize_resume(
        self,
        *,
        user: User,
        course_id: str,
        evidence_id: str,
        session: Session,
    ) -> ResumeOptimizationResponse:
        candidate = CandidateRepository(session).get_or_create_for_user(user)
        course = session.get(CourseRecord, course_id)
        if course is None or course.candidate_id != str(candidate.id):
            raise NotFoundError("Course not found", {"course_id": course_id})
        evidence = session.get(EvidenceRecord, evidence_id)
        if evidence is None or evidence.candidate_id != str(candidate.id):
            raise NotFoundError("Resume evidence not found", {"evidence_id": evidence_id})
        if evidence.source_type != "CV" or not evidence.content:
            raise NotFoundError("A text CV evidence record is required", {"evidence_id": evidence_id})
        skills = _course_skills(course)
        raw_result = await self._gateway.optimize_resume(
            resume_text=evidence.content, newly_learned_skills=skills
        )
        result = _validate_resume(raw_result, evidence.content, skills)

        latest_version = session.scalar(
            select(ResumeRecord.version)
            .where(
                ResumeRecord.candidate_id == str(candidate.id),
                ResumeRecord.template == "intelligence-optimized",
            )
            .order_by(ResumeRecord.version.desc())
            .limit(1)
        )
        resume = ResumeRecord(
            id=str(uuid4()),
            candidate_id=str(candidate.id),
            job_id=course.job_id,
            template="intelligence-optimized",
            version=int(latest_version or 0) + 1,
            content={
                "original_resume_text": result.original_resume_text,
                "updated_resume_text": result.updated_resume_text,
                "injected_skills": skills,
                "summary_of_changes": result.summary_of_changes,
                "source_course_id": course.id,
            },
            evidence_references=[str(evidence.id)],
        )
        session.add(resume)
        session.commit()
        return ResumeOptimizationResponse(
            resume_id=UUID(resume.id),
            version=resume.version,
            evidence_references=[UUID(str(evidence.id))],
            result=result,
        )


def _validate_interview_result(raw_result: Mapping[str, Any]) -> NormalizedInterviewResult:
    try:
        return NormalizedInterviewResult.model_validate(raw_result)
    except ValidationError as exc:
        raise InvalidIntelligenceOutputError(details={"reason": "stored interview result is invalid"}) from exc


def _validate_course(raw_course: Mapping[str, Any]) -> NormalizedCourse:
    if hasattr(raw_course, "model_dump"):
        raw_course = raw_course.model_dump()
    try:
        return NormalizedCourse.model_validate(raw_course)
    except (ValidationError, TypeError) as exc:
        raise InvalidIntelligenceOutputError(details={"reason": "course schema validation failed"}) from exc


def _validate_resume(
    raw_result: Mapping[str, Any], source_text: str, allowed_skills: list[str]
) -> NormalizedResumeOptimization:
    if hasattr(raw_result, "model_dump"):
        raw_result = raw_result.model_dump()
    try:
        result = NormalizedResumeOptimization.model_validate(raw_result)
    except (ValidationError, TypeError) as exc:
        raise InvalidIntelligenceOutputError(details={"reason": "resume schema validation failed"}) from exc
    if result.original_resume_text != source_text:
        raise InvalidIntelligenceOutputError(details={"reason": "resume source text changed at boundary"})
    allowed = {skill.casefold() for skill in allowed_skills}
    if any(skill.casefold() not in allowed for skill in result.injected_skills):
        raise InvalidIntelligenceOutputError(details={"reason": "resume output contains unrequested skills"})
    return result


def _course_skills(course: CourseRecord) -> list[str]:
    skills: list[str] = []
    for module in course.module_rows:
        skill = (module.content or {}).get("skill_name")
        if isinstance(skill, str) and skill.strip() and skill.strip() not in skills:
            skills.append(skill.strip())
    if not skills:
        raise InvalidIntelligenceOutputError(details={"reason": "course has no persisted skills"})
    return skills


def _string_items(items: Sequence[Any]) -> list[str]:
    return [item.strip() for item in items if isinstance(item, str) and item.strip()]
