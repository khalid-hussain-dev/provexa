from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.errors import NotFoundError
from app.database.models import (
    CandidateRecord,
    InterviewAnswerRecord,
    InterviewQuestionRecord,
    InterviewRecord,
    JobRecord,
)

from .errors import IncompleteInterviewError, InvalidIntelligenceOutputError
from .interview_persistence import InterviewIntegrationRepository
from .profile_persistence import ProfileAnalysisSnapshotRecord


class InterviewQuestionInput(BaseModel):
    question: str = Field(min_length=1, max_length=10000)
    category: str = Field(min_length=1, max_length=120)
    difficulty: str = Field(default="medium", min_length=1, max_length=32)


class InterviewResponseInput(BaseModel):
    question_id: str
    answer: str = Field(min_length=1, max_length=10000)
    confidence: int = Field(default=5, ge=1, le=10)


class NormalizedSkillAssessment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    skill_name: str = ""
    percentage: float = Field(default=0, ge=0, le=100)
    strength_level: str = "beginner"
    evidence: list[str] = Field(default_factory=list)


class NormalizedStrengthWeakness(BaseModel):
    model_config = ConfigDict(extra="ignore")

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    improvement_areas: list[Any] = Field(default_factory=list)


class NormalizedCourseRecommendation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = ""
    description: str = ""
    duration_weeks: int = Field(default=0, ge=0)
    topics: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    priority: str = "medium"


class NormalizedInterviewResult(BaseModel):
    """Allowlisted Intelligence result kept compatible with its existing semantics."""

    model_config = ConfigDict(extra="ignore")

    candidate_name: str = "Unknown"
    target_role: str = "Unknown"
    overall_score: float = Field(ge=0, le=100)
    assessed_level: str = "junior"
    skill_assessments: list[NormalizedSkillAssessment] = Field(default_factory=list)
    analysis: NormalizedStrengthWeakness
    course_recommendations: list[NormalizedCourseRecommendation] = Field(default_factory=list)
    interview_summary: str = ""
    role_match_percentage: float = Field(default=0, ge=0, le=100)

    @model_validator(mode="after")
    def require_result_content(self) -> "NormalizedInterviewResult":
        if not self.interview_summary and not self.skill_assessments and not (
            self.analysis.strengths or self.analysis.weaknesses or self.analysis.improvement_areas
        ):
            raise ValueError("interview result contains no evaluative content")
        return self


class InterviewQuestionResponse(BaseModel):
    question_id: UUID
    question: str
    category: str
    difficulty: str


class InterviewCreateResponse(BaseModel):
    interview_id: UUID
    status: str = "CREATED"
    total_questions: int
    first_question: InterviewQuestionResponse


class InterviewAnswerAcceptedResponse(BaseModel):
    interview_id: UUID
    question_id: UUID
    status: str = "RECORDED"
    next_question: InterviewQuestionResponse | None = None


class InterviewEvaluationResponse(BaseModel):
    evaluation_id: UUID
    interview_id: UUID
    status: str = "COMPLETED"
    result: NormalizedInterviewResult


class InterviewAnalysisGateway(Protocol):
    async def generate_questions(
        self, profile_context: Mapping[str, Any], num_questions: int
    ) -> Sequence[Any]: ...

    async def evaluate(
        self,
        profile_context: Mapping[str, Any],
        questions: Sequence[InterviewQuestionInput],
        responses: Sequence[InterviewResponseInput],
    ) -> Mapping[str, Any]: ...


class IntelligenceInterviewGateway:
    """Lazy bridge to the unchanged Intelligence InterviewSystem methods."""

    def __init__(self, intelligence_system: Any | None = None) -> None:
        self._intelligence_system = intelligence_system

    def _system(self) -> tuple[Any, Any]:
        if self._intelligence_system is None:
            from interview_system import InterviewSystem

            self._intelligence_system = InterviewSystem()
        from models import InterviewQuestion, InterviewResponse

        return self._intelligence_system, (InterviewQuestion, InterviewResponse)

    async def generate_questions(
        self, profile_context: Mapping[str, Any], num_questions: int
    ) -> Sequence[Any]:
        system, _ = self._system()
        return await system.generate_interview_questions(dict(profile_context), num_questions)

    async def evaluate(
        self,
        profile_context: Mapping[str, Any],
        questions: Sequence[InterviewQuestionInput],
        responses: Sequence[InterviewResponseInput],
    ) -> Mapping[str, Any]:
        system, (question_model, response_model) = self._system()
        intelligence_questions = [question_model(**question.model_dump()) for question in questions]
        intelligence_responses = [response_model(**response.model_dump()) for response in responses]
        result = await system.evaluate_interview_responses(
            dict(profile_context), intelligence_questions, intelligence_responses
        )
        return result.model_dump() if hasattr(result, "model_dump") else result


class InterviewAdapter:
    def __init__(self, gateway: InterviewAnalysisGateway) -> None:
        self._gateway = gateway

    async def create(
        self,
        *,
        user: User,
        candidate: CandidateRecord,
        job: JobRecord,
        num_questions: int,
        session: Session,
    ) -> InterviewCreateResponse:
        snapshot = _latest_snapshot(session, str(candidate.id))
        if snapshot is None:
            raise NotFoundError(
                "Run profile analysis before starting an Intelligence interview",
                {"candidate_id": str(candidate.id)},
            )

        profile_context = _interview_context(snapshot.profile_context, candidate, job, user)
        raw_questions = await self._gateway.generate_questions(profile_context, num_questions)
        questions = _validate_questions(raw_questions, num_questions)

        interview = InterviewRecord(
            id=str(uuid4()), candidate_id=str(candidate.id), job_id=str(job.id), status="CREATED"
        )
        session.add(interview)
        session.flush()
        InterviewIntegrationRepository(session).create_context(
            interview_id=interview.id,
            profile_snapshot_id=snapshot.id,
            profile_context=dict(profile_context),
        )
        records = []
        for index, question in enumerate(questions, start=1):
            record = InterviewQuestionRecord(
                    id=str(uuid4()),
                    interview_id=interview.id,
                    sequence=index,
                    question=question.question,
                    competency=question.category,
                    difficulty=question.difficulty,
                    expected_signals=[],
                )
            records.append(record)
            session.add(record)
        session.commit()
        return InterviewCreateResponse(
            interview_id=UUID(interview.id),
            total_questions=len(questions),
            first_question=_question_response(records[0]),
        )

    def record_answer(
        self,
        *,
        interview: InterviewRecord,
        question_id: str,
        answer: str,
        confidence: int,
        session: Session,
    ) -> InterviewAnswerAcceptedResponse:
        question = session.get(InterviewQuestionRecord, question_id)
        if question is None or question.interview_id != interview.id:
            raise NotFoundError("Interview question not found", {"question_id": question_id})
        existing = session.scalar(
            select(InterviewAnswerRecord).where(
                InterviewAnswerRecord.interview_id == interview.id,
                InterviewAnswerRecord.question_id == question_id,
            )
        )
        if existing is None:
            existing = InterviewAnswerRecord(
                id=str(uuid4()),
                interview_id=interview.id,
                question_id=question_id,
                answer=answer,
            )
            session.add(existing)
        else:
            existing.answer = answer
        existing.feedback = f"Answer recorded with confidence {confidence}/10 for Intelligence evaluation."
        interview.status = "IN_PROGRESS"
        interview.current_question_index = max(interview.current_question_index, question.sequence)
        next_record = session.scalar(
            select(InterviewQuestionRecord).where(
                InterviewQuestionRecord.interview_id == interview.id,
                InterviewQuestionRecord.sequence == question.sequence + 1,
            )
        )
        session.commit()
        return InterviewAnswerAcceptedResponse(
            interview_id=UUID(interview.id),
            question_id=UUID(question.id),
            next_question=_question_response(next_record) if next_record else None,
        )

    async def complete(
        self, *, interview: InterviewRecord, session: Session
    ) -> InterviewEvaluationResponse:
        repository = InterviewIntegrationRepository(session)
        existing = repository.get_evaluation(interview.id)
        if existing is not None:
            return _evaluation_response(existing)
        context = repository.get_context(interview.id)
        if context is None:
            raise NotFoundError("Interview integration context not found")

        questions = list(
            session.scalars(
                select(InterviewQuestionRecord)
                .where(InterviewQuestionRecord.interview_id == interview.id)
                .order_by(InterviewQuestionRecord.sequence)
            )
        )
        answer_rows = {
            row.question_id: row
            for row in session.scalars(
                select(InterviewAnswerRecord).where(
                    InterviewAnswerRecord.interview_id == interview.id
                )
            )
        }
        if len(answer_rows) != len(questions):
            raise IncompleteInterviewError()
        question_inputs = [_question_input(question) for question in questions]
        response_inputs = [
            InterviewResponseInput(
                question_id=question.id,
                answer=answer_rows[question.id].answer,
                confidence=5,
            )
            for question in questions
        ]
        raw_result = await self._gateway.evaluate(
            context.profile_context, question_inputs, response_inputs
        )
        result = _validate_result(raw_result)
        evaluation_id = str(uuid4())
        repository.create_evaluation(
            evaluation_id=evaluation_id,
            interview_id=interview.id,
            profile_snapshot_id=context.profile_snapshot_id,
            result=result.model_dump(mode="json"),
        )
        interview.status = "COMPLETED"
        interview.overall_score = result.overall_score
        from datetime import datetime, timezone

        interview.completed_at = datetime.now(timezone.utc)
        session.commit()
        return InterviewEvaluationResponse(
            evaluation_id=UUID(evaluation_id),
            interview_id=UUID(interview.id),
            result=result,
        )


def _latest_snapshot(session: Session, candidate_id: str) -> ProfileAnalysisSnapshotRecord | None:
    return session.scalar(
        select(ProfileAnalysisSnapshotRecord)
        .where(ProfileAnalysisSnapshotRecord.candidate_id == candidate_id)
        .order_by(ProfileAnalysisSnapshotRecord.created_at.desc())
    )


def _interview_context(
    profile_context: Mapping[str, Any],
    candidate: CandidateRecord,
    job: JobRecord,
    user: User,
) -> dict[str, Any]:
    context = dict(profile_context)
    context["name"] = context.get("name") or candidate.name or user.name or user.email
    context["target_role"] = context.get("target_role") or candidate.headline or job.title
    context["target_job"] = {
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "requirements": [requirement.skill_name for requirement in job.requirements],
    }
    return context


def _validate_questions(raw_questions: Sequence[Any], num_questions: int) -> list[InterviewQuestionInput]:
    if not isinstance(raw_questions, Sequence) or isinstance(raw_questions, (str, bytes)):
        raise InvalidIntelligenceOutputError(details={"reason": "questions must be a list"})
    if not raw_questions or len(raw_questions) > num_questions:
        raise InvalidIntelligenceOutputError(details={"reason": "question count is invalid"})
    normalized: list[InterviewQuestionInput] = []
    try:
        for item in raw_questions:
            payload = item.model_dump() if hasattr(item, "model_dump") else item
            normalized.append(InterviewQuestionInput.model_validate(payload))
    except (ValidationError, TypeError) as exc:
        raise InvalidIntelligenceOutputError(details={"reason": "question schema validation failed"}) from exc
    return normalized


def _validate_result(raw_result: Mapping[str, Any]) -> NormalizedInterviewResult:
    if hasattr(raw_result, "model_dump"):
        raw_result = raw_result.model_dump()
    if not isinstance(raw_result, Mapping):
        raise InvalidIntelligenceOutputError(details={"reason": "interview result must be an object"})
    try:
        return NormalizedInterviewResult.model_validate(raw_result)
    except ValidationError as exc:
        raise InvalidIntelligenceOutputError(
            details={"reason": "interview result schema validation failed", "fields": exc.error_count()}
        ) from exc


def _question_input(record: InterviewQuestionRecord) -> InterviewQuestionInput:
    return InterviewQuestionInput(
        question=record.question, category=record.competency, difficulty=record.difficulty
    )


def _question_response(record: InterviewQuestionRecord) -> InterviewQuestionResponse:
    return InterviewQuestionResponse(
        question_id=UUID(record.id),
        question=record.question,
        category=record.competency,
        difficulty=record.difficulty,
    )


def _evaluation_response(record) -> InterviewEvaluationResponse:
    return InterviewEvaluationResponse(
        evaluation_id=UUID(record.id), interview_id=UUID(record.interview_id), result=_validate_result(record.result)
    )
