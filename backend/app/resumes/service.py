from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import CapabilityRecord, EvidenceRecord, ResumeRecord

TEMPLATES = [
    {"id": "minimal", "name": "Minimal Professional", "preview": None},
]


class ResumeService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_templates(self) -> list[dict]:
        return TEMPLATES

    def generate_resume(self, candidate, job, template: str) -> ResumeRecord:
        evidence_items = list(self._session.scalars(select(EvidenceRecord).where(EvidenceRecord.candidate_id == candidate.id)))
        capabilities = list(self._session.scalars(select(CapabilityRecord).where(CapabilityRecord.candidate_id == candidate.id)))
        skills = [capability.skill_name for capability in capabilities]
        evidence_references = [str(item.id) for item in evidence_items]

        latest_version = self._session.scalar(
            select(ResumeRecord.version)
            .where(ResumeRecord.candidate_id == candidate.id, ResumeRecord.template == template)
            .order_by(ResumeRecord.version.desc())
            .limit(1)
        )
        version = int(latest_version or 0) + 1
        target_title = job.title if job else "target role"
        content = {
            "header": {
                "name": candidate.name,
                "headline": candidate.headline,
                "location": candidate.location,
            },
            "summary": candidate.summary or f"Evidence-backed resume tailored for {target_title}.",
            "skills": skills,
            "experience_highlights": [
                {
                    "title": item.title,
                    "source_type": item.source_type,
                    "evidence_id": str(item.id),
                }
                for item in evidence_items
            ],
            "target_role": job.title if job else None,
            "template": template,
        }

        resume = ResumeRecord(
            id=str(uuid4()),
            candidate_id=candidate.id,
            job_id=job.id if job else None,
            template=template,
            version=version,
            content=content,
            evidence_references=evidence_references,
        )
        self._session.add(resume)
        self._session.commit()
        self._session.refresh(resume)
        return resume
