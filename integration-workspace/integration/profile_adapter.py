from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.database.models import CandidateRecord, EvidenceRecord

from .errors import InvalidIntelligenceOutputError
from .profile_persistence import ProfileAnalysisSnapshotRepository


class CandidateProfileInput(BaseModel):
    """The exact input shape expected by Intelligence's CandidateProfile model."""

    name: str
    email: str
    resume_text: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    experience_years: float = Field(default=0, ge=0)
    skills: list[str] = Field(default_factory=list)
    target_role: str
    additional_info: str | None = None

    @field_validator("name", "email", "target_role")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return value.strip()


class ProfileContext(BaseModel):
    """Allowlisted, normalized fields from Intelligence profile synthesis."""

    model_config = ConfigDict(extra="ignore")

    candidate_summary: str | None = None
    primary_domain: str | None = None
    secondary_domains: list[str] = Field(default_factory=list)
    domain_confidence: float | None = Field(default=None, ge=0, le=100)
    all_skills: list[str] = Field(default_factory=list)
    skill_clusters: dict[str, list[str]] = Field(default_factory=dict)
    technical_strengths: list[str] = Field(default_factory=list)
    potential_weaknesses: list[str] = Field(default_factory=list)
    interview_readiness: str | None = None
    recommended_interview_depth: str | None = None
    profile_context: str | None = None

    @model_validator(mode="after")
    def require_meaningful_context(self) -> "ProfileContext":
        if not any((self.candidate_summary, self.primary_domain, self.all_skills, self.profile_context)):
            raise ValueError("profile output contains no usable context")
        return self


class ProfileAnalysisResponse(BaseModel):
    analysis_id: UUID
    status: str = "completed"
    source_evidence_ids: list[UUID] = Field(default_factory=list)
    profile_context: ProfileContext


class ProfileAnalysisGateway(Protocol):
    async def analyze(self, candidate: CandidateProfileInput) -> Mapping[str, Any]: ...


class IntelligenceProfileGateway:
    """Lazy bridge to the existing Intelligence workflow; it does not alter that workflow."""

    def __init__(self, intelligence_system: Any | None = None) -> None:
        self._intelligence_system = intelligence_system

    async def analyze(self, candidate: CandidateProfileInput) -> Mapping[str, Any]:
        if self._intelligence_system is None:
            from models import CandidateProfile
            from interview_system import InterviewSystem

            self._intelligence_system = InterviewSystem()
            intelligence_candidate = CandidateProfile(**candidate.model_dump())
        else:
            intelligence_candidate = candidate
        return await self._intelligence_system.prepare_candidate_profile(intelligence_candidate)


@dataclass(frozen=True)
class MappedCandidateProfile:
    candidate: CandidateProfileInput
    evidence_ids: list[str]


class CandidateProfileMapper:
    def map(
        self,
        user: User,
        candidate: CandidateRecord,
        evidence: list[EvidenceRecord],
    ) -> MappedCandidateProfile:
        preferences = candidate.preferences or {}
        skills = _string_list(preferences.get("skills"))
        resume_parts = [item.content for item in evidence if item.source_type == "CV" and item.content]
        github_url = _first_external_url(evidence, "GITHUB")
        portfolio_url = _first_external_url(evidence, "PORTFOLIO")
        linkedin_url = _metadata_url(evidence, "linkedin_url")
        target_role = _string_value(preferences.get("target_role")) or candidate.headline or "Unspecified"
        experience_years = _number_value(preferences.get("experience_years"), default=0.0)
        name = candidate.name or user.name or user.email.split("@", 1)[0]

        return MappedCandidateProfile(
            candidate=CandidateProfileInput(
                name=name,
                email=user.email,
                resume_text="\n\n".join(resume_parts) or None,
                github_url=github_url,
                linkedin_url=linkedin_url,
                portfolio_url=portfolio_url,
                experience_years=experience_years,
                skills=skills,
                target_role=target_role,
                additional_info=candidate.summary,
            ),
            evidence_ids=[str(item.id) for item in evidence],
        )


class CandidateProfileAnalysisAdapter:
    def __init__(
        self,
        gateway: ProfileAnalysisGateway,
        mapper: CandidateProfileMapper | None = None,
    ) -> None:
        self._gateway = gateway
        self._mapper = mapper or CandidateProfileMapper()

    async def analyze_and_persist(
        self,
        *,
        user: User,
        candidate: CandidateRecord,
        session: Session,
    ) -> ProfileAnalysisResponse:
        evidence = list(
            session.scalars(
                select(EvidenceRecord)
                .where(EvidenceRecord.candidate_id == str(candidate.id))
                .order_by(EvidenceRecord.created_at)
            )
        )
        mapped = self._mapper.map(user, candidate, evidence)
        raw_result = await self._gateway.analyze(mapped.candidate)
        profile_context = _validate_profile_context(raw_result)
        analysis_id = uuid4()
        ProfileAnalysisSnapshotRepository(session).create(
            analysis_id=str(analysis_id),
            candidate_id=str(candidate.id),
            source_evidence_ids=mapped.evidence_ids,
            profile_context=profile_context.model_dump(mode="json"),
        )
        return ProfileAnalysisResponse(
            analysis_id=analysis_id,
            source_evidence_ids=[UUID(item) for item in mapped.evidence_ids],
            profile_context=profile_context,
        )


def _validate_profile_context(raw_result: Mapping[str, Any]) -> ProfileContext:
    if not isinstance(raw_result, Mapping):
        raise InvalidIntelligenceOutputError(details={"reason": "result must be an object"})
    try:
        return ProfileContext.model_validate(raw_result)
    except ValidationError as exc:
        raise InvalidIntelligenceOutputError(
            details={"reason": "profile context schema validation failed", "fields": exc.error_count()}
        ) from exc


def _string_value(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _number_value(value: Any, *, default: float) -> float:
    if isinstance(value, bool):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number >= 0 else default


def _first_external_url(evidence: list[EvidenceRecord], source_type: str) -> str | None:
    for item in evidence:
        if item.source_type == source_type and item.external_url:
            return item.external_url
    return None


def _metadata_url(evidence: list[EvidenceRecord], key: str) -> str | None:
    for item in evidence:
        value = (item.metadata_json or {}).get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
