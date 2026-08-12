from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.service import AnalysisService
from app.auth.models import User
from app.candidates.repository import CandidateRepository
from app.database.models import CapabilityRecord, JobRecord
from app.jobs.repository import JobRepository


@dataclass(frozen=True)
class JobRecommendation:
    job: JobRecord
    match_score: int
    readiness_score: int


class JobService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repository = JobRepository(session)

    def list_jobs(self, *, page: int, limit: int, source: str | None, query: str | None, location: str | None) -> tuple[list[JobRecord], int]:
        return self._repository.list_jobs(page=page, limit=limit, source=source, query=query, location=location)

    def get_job(self, job_id: str) -> JobRecord | None:
        return self._repository.get_job(job_id)

    def recommend_jobs(self, user: User, *, limit: int, location: str | None) -> list[JobRecommendation]:
        candidate = CandidateRepository(self._session).get_or_create_for_user(user)
        if not list(self._session.scalars(select(CapabilityRecord).where(CapabilityRecord.candidate_id == candidate.id))):
            AnalysisService(self._session).analyze_candidate(candidate)

        jobs, _ = self._repository.list_jobs(page=1, limit=100, source=None, query=None, location=location)
        recommendations = [self._score_job(candidate.id, job) for job in jobs]
        recommendations.sort(key=lambda item: (-item.match_score, item.job.created_at, item.job.title))
        return recommendations[:limit]

    def _score_job(self, candidate_id: str, job: JobRecord) -> JobRecommendation:
        requirements = self._repository.get_requirements(job.id)
        capabilities = {
            capability.skill_name.lower(): capability
            for capability in self._session.scalars(select(CapabilityRecord).where(CapabilityRecord.candidate_id == candidate_id))
        }
        if not capabilities:
            return JobRecommendation(job=job, match_score=0, readiness_score=0)

        weighted_scores: list[float] = []
        gaps = 0
        for requirement in requirements:
            capability = capabilities.get(requirement.skill_name.lower())
            score = capability.evidence_score if capability else 0.0
            weighted_scores.append(score * (requirement.importance / 100))
            if score < 65:
                gaps += 1
        divisor = sum(requirement.importance / 100 for requirement in requirements) or 1
        match_score = round(sum(weighted_scores) / divisor)
        readiness_score = max(0, min(100, match_score - (gaps * 4)))
        return JobRecommendation(job=job, match_score=match_score, readiness_score=readiness_score)
