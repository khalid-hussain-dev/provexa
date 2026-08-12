from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.session import Base

JsonType = JSON().with_variant(JSONB, "postgresql")
UuidType = String(36).with_variant(PostgresUUID(as_uuid=False), "postgresql")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def uuid_str() -> str:
    return str(uuid4())


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_factor_secret: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    candidate: Mapped["CandidateRecord | None"] = relationship(back_populates="user")
    subscriptions: Mapped[list["SubscriptionRecord"]] = relationship(back_populates="user")


class PasswordResetTokenRecord(Base):
    __tablename__ = "password_reset_tokens"

    token_hash: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(UuidType, ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class RevokedTokenRecord(Base):
    __tablename__ = "revoked_tokens"

    token_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class CandidateRecord(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(UuidType, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferences: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user: Mapped[UserRecord] = relationship(back_populates="candidate")

    interviews: Mapped[list["InterviewRecord"]] = relationship(back_populates="candidate")
    courses: Mapped[list["CourseRecord"]] = relationship(back_populates="candidate")
    resumes: Mapped[list["ResumeRecord"]] = relationship(back_populates="candidate")


class EvidenceRecord(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    candidate_id: Mapped[str] = mapped_column(UuidType, ForeignKey("candidates.id"), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JsonType, default=dict, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="CLAIMED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class CapabilityRecord(Base):
    __tablename__ = "capabilities"
    __table_args__ = (UniqueConstraint("candidate_id", "skill_name", name="uq_candidate_skill"),)

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    candidate_id: Mapped[str] = mapped_column(UuidType, ForeignKey("candidates.id"), index=True, nullable=False)
    skill_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    claimed_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    demonstrated_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="CLAIMED", nullable=False)
    evidence_ids: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class JobRecord(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    seniority: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source: Mapped[str] = mapped_column(String(120), default="demo", nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    responsibilities: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JsonType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    requirements: Mapped[list["JobRequirementRecord"]] = relationship(back_populates="job")
    interviews: Mapped[list["InterviewRecord"]] = relationship(back_populates="job")
    courses: Mapped[list["CourseRecord"]] = relationship(back_populates="job")
    resumes: Mapped[list["ResumeRecord"]] = relationship(back_populates="job")


class JobRequirementRecord(Base):
    __tablename__ = "job_requirements"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    job_id: Mapped[str] = mapped_column(UuidType, ForeignKey("jobs.id"), index=True, nullable=False)
    skill_name: Mapped[str] = mapped_column(String(120), nullable=False)
    importance: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    requirement_type: Mapped[str] = mapped_column(String(32), default="REQUIRED", nullable=False)
    evidence_expectation: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JsonType, default=dict, nullable=False)

    job: Mapped[JobRecord] = relationship(back_populates="requirements")


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    candidate_id: Mapped[str] = mapped_column(UuidType, ForeignKey("candidates.id"), index=True, nullable=False)
    job_id: Mapped[str] = mapped_column(UuidType, ForeignKey("jobs.id"), index=True, nullable=False)
    match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    strengths: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    gaps: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    evidence_summary: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    recommendations: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    model_metadata: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class InterviewRecord(Base):
    __tablename__ = "interviews"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    candidate_id: Mapped[str] = mapped_column(UuidType, ForeignKey("candidates.id"), index=True, nullable=False)
    job_id: Mapped[str] = mapped_column(UuidType, ForeignKey("jobs.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="CREATED", nullable=False)
    current_question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    technical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    communication_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    problem_solving_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    role_alignment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    verdict: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    candidate: Mapped[CandidateRecord] = relationship(back_populates="interviews")
    job: Mapped[JobRecord] = relationship(back_populates="interviews")
    questions: Mapped[list["InterviewQuestionRecord"]] = relationship(back_populates="interview", cascade="all, delete-orphan")
    answers: Mapped[list["InterviewAnswerRecord"]] = relationship(back_populates="interview", cascade="all, delete-orphan")


class CourseRecord(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    candidate_id: Mapped[str] = mapped_column(UuidType, ForeignKey("candidates.id"), index=True, nullable=False)
    job_id: Mapped[str] = mapped_column(UuidType, ForeignKey("jobs.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_duration: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="GENERATED", nullable=False)
    modules: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    candidate: Mapped[CandidateRecord] = relationship(back_populates="courses")
    job: Mapped[JobRecord] = relationship(back_populates="courses")
    progress_entries: Mapped[list["LearningProgressRecord"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    module_rows: Mapped[list["CourseModuleRecord"]] = relationship(back_populates="course", cascade="all, delete-orphan")


class ResumeRecord(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    candidate_id: Mapped[str] = mapped_column(UuidType, ForeignKey("candidates.id"), index=True, nullable=False)
    job_id: Mapped[str | None] = mapped_column(UuidType, ForeignKey("jobs.id"), nullable=True)
    template: Mapped[str] = mapped_column(String(120), default="minimal", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    content: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    evidence_references: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    candidate: Mapped[CandidateRecord] = relationship(back_populates="resumes")
    job: Mapped[JobRecord | None] = relationship(back_populates="resumes")


class SubscriptionRecord(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(UuidType, ForeignKey("users.id"), index=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    provider: Mapped[str] = mapped_column(String(64), default="demo", nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[UserRecord] = relationship(back_populates="subscriptions")


class InterviewQuestionRecord(Base):
    __tablename__ = "interview_questions"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    interview_id: Mapped[str] = mapped_column(UuidType, ForeignKey("interviews.id"), index=True, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    competency: Mapped[str] = mapped_column(String(120), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), default="MEDIUM", nullable=False)
    expected_signals: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)

    interview: Mapped[InterviewRecord] = relationship(back_populates="questions")


class InterviewAnswerRecord(Base):
    __tablename__ = "interview_answers"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    interview_id: Mapped[str] = mapped_column(UuidType, ForeignKey("interviews.id"), index=True, nullable=False)
    question_id: Mapped[str] = mapped_column(UuidType, ForeignKey("interview_questions.id"), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    strengths: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    weaknesses: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    interview: Mapped[InterviewRecord] = relationship(back_populates="answers")


class CourseModuleRecord(Base):
    __tablename__ = "course_modules"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    course_id: Mapped[str] = mapped_column(UuidType, ForeignKey("courses.id"), index=True, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    challenge: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)

    course: Mapped[CourseRecord] = relationship(back_populates="module_rows")


class LearningProgressRecord(Base):
    __tablename__ = "learning_progress"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True, default=uuid_str)
    course_id: Mapped[str] = mapped_column(UuidType, ForeignKey("courses.id"), index=True, nullable=False)
    module_id: Mapped[str] = mapped_column(UuidType, ForeignKey("course_modules.id"), nullable=False)
    completion_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    assessment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    course: Mapped[CourseRecord] = relationship(back_populates="progress_entries")
