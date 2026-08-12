from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import AnalysisRecord, CandidateRecord, CapabilityRecord, EvidenceRecord, JobRecord, JobRequirementRecord
from app.core.errors import NotFoundError

SKILL_KEYWORDS = {
    "Python": ["python", "fastapi", "django", "flask"],
    "FastAPI": ["fastapi"],
    "PostgreSQL": ["postgres", "postgresql", "sql"],
    "Redis": ["redis", "cache", "caching"],
    "Docker": ["docker", "container"],
    "React": ["react", "next.js", "nextjs"],
    "GitHub": ["github", "repository", "repositories"],
    "Kubernetes": ["kubernetes", "k8s"],
    "API Design": ["api", "rest", "openapi"],
    "Testing": ["pytest", "testing", "tests"],
}


class AnalysisService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def analyze_candidate(self, candidate: CandidateRecord) -> tuple[str, list[dict]]:
        evidence_items = list(self._session.scalars(select(EvidenceRecord).where(EvidenceRecord.candidate_id == candidate.id)))
        text = " ".join(filter(None, [item.title + " " + (item.content or "") for item in evidence_items])).lower()
        capabilities: list[dict] = []
        for skill, keywords in SKILL_KEYWORDS.items():
            hits = sum(1 for keyword in keywords if keyword in text)
            if hits == 0:
                continue
            score = min(100, 45 + (hits * 15))
            status = "STRONG" if score >= 80 else "SUPPORTED"
            record = self._upsert_capability(candidate.id, skill, score, status, [str(item.id) for item in evidence_items])
            capabilities.append(_capability_payload(record))
        self._session.commit()
        return str(uuid4()), capabilities

    def analyze_job(self, payload: dict) -> tuple[JobRecord, list[dict]]:
        job = JobRecord(
            title=payload["title"].strip(),
            company=payload["company"].strip(),
            description=payload["job_description"].strip(),
            source="user_input",
            responsibilities=[],
            metadata_json={},
        )
        self._session.add(job)
        self._session.flush()

        requirements: list[dict] = []
        text = f"{job.title} {job.description}".lower()
        for skill, keywords in SKILL_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                requirement = JobRequirementRecord(
                    id=str(uuid4()),
                    job_id=job.id,
                    skill_name=skill,
                    importance=85.0 if skill in {"Python", "FastAPI", "PostgreSQL"} else 70.0,
                    requirement_type="REQUIRED",
                    evidence_expectation=f"Evidence showing practical {skill} experience",
                    metadata_json={},
                )
                self._session.add(requirement)
                requirements.append(_requirement_payload(requirement))
        if not requirements:
            requirement = JobRequirementRecord(
                id=str(uuid4()),
                job_id=job.id,
                skill_name="API Design",
                importance=70.0,
                requirement_type="REQUIRED",
                evidence_expectation="Evidence showing backend API delivery",
                metadata_json={},
            )
            self._session.add(requirement)
            requirements.append(_requirement_payload(requirement))

        self._session.commit()
        self._session.refresh(job)
        return job, requirements

    def match_candidate_to_job(self, candidate: CandidateRecord, job_id: str) -> dict:
        job = self._session.get(JobRecord, job_id)
        if not job:
            raise NotFoundError("Job not found", {"job_id": job_id})

        requirements = list(self._session.scalars(select(JobRequirementRecord).where(JobRequirementRecord.job_id == job_id)))
        capabilities = {
            capability.skill_name.lower(): capability
            for capability in self._session.scalars(select(CapabilityRecord).where(CapabilityRecord.candidate_id == candidate.id))
        }
        if not capabilities:
            self.analyze_candidate(candidate)
            capabilities = {
                capability.skill_name.lower(): capability
                for capability in self._session.scalars(select(CapabilityRecord).where(CapabilityRecord.candidate_id == candidate.id))
            }

        strengths: list[dict] = []
        gaps: list[dict] = []
        weighted_scores: list[float] = []
        for requirement in requirements:
            capability = capabilities.get(requirement.skill_name.lower())
            candidate_score = capability.evidence_score if capability else 0.0
            weighted_scores.append(candidate_score * (requirement.importance / 100))
            if candidate_score >= 65:
                strengths.append({"skill": requirement.skill_name, "score": round(candidate_score), "evidence": capability.evidence_ids if capability else []})
            else:
                gaps.append(
                    {
                        "skill": requirement.skill_name,
                        "required_score": 80,
                        "candidate_score": round(candidate_score),
                        "importance": round(requirement.importance),
                    }
                )

        divisor = sum(requirement.importance / 100 for requirement in requirements) or 1
        match_score = round(sum(weighted_scores) / divisor)
        readiness_score = max(0, min(100, match_score - (len(gaps) * 4)))
        recommendations = [{"skill": gap["skill"], "action": f"Add stronger evidence or practice for {gap['skill']}"} for gap in gaps[:3]]
        evidence_summary = [{"skill": item["skill"], "score": item["score"]} for item in strengths]

        analysis = AnalysisRecord(
            id=str(uuid4()),
            candidate_id=candidate.id,
            job_id=job.id,
            match_score=match_score,
            readiness_score=readiness_score,
            strengths=strengths,
            gaps=gaps,
            evidence_summary=evidence_summary,
            recommendations=recommendations,
            model_metadata={"provider": "deterministic-platform-stub"},
        )
        self._session.add(analysis)
        self._session.commit()
        self._session.refresh(analysis)
        return {
            "analysis_id": analysis.id,
            "match_score": match_score,
            "readiness_score": readiness_score,
            "strengths": strengths,
            "gaps": gaps,
            "recommendations": recommendations,
            "evidence_summary": evidence_summary,
        }

    def _upsert_capability(self, candidate_id: str, skill: str, score: float, status: str, evidence_ids: list[str]) -> CapabilityRecord:
        record = self._session.scalar(
            select(CapabilityRecord).where(CapabilityRecord.candidate_id == candidate_id, CapabilityRecord.skill_name == skill)
        )
        if record is None:
            record = CapabilityRecord(candidate_id=candidate_id, skill_name=skill)
            self._session.add(record)
        record.category = "technical"
        record.claimed_score = score
        record.evidence_score = score
        record.demonstrated_score = 0.0
        record.confidence = min(1.0, score / 100)
        record.status = status
        record.evidence_ids = evidence_ids
        return record


def _capability_payload(record: CapabilityRecord) -> dict:
    return {
        "id": str(record.id),
        "skill_name": record.skill_name,
        "category": record.category,
        "claimed_score": round(record.claimed_score),
        "evidence_score": round(record.evidence_score),
        "demonstrated_score": round(record.demonstrated_score),
        "confidence": record.confidence,
        "status": record.status,
        "evidence_ids": record.evidence_ids,
    }


def _requirement_payload(record: JobRequirementRecord) -> dict:
    return {
        "id": str(record.id) if record.id else None,
        "skill_name": record.skill_name,
        "importance": round(record.importance),
        "requirement_type": record.requirement_type,
        "evidence_expectation": record.evidence_expectation,
    }
