from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.database.models import CandidateRecord, EvidenceRecord


class CandidateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_or_create_for_user(self, user: User) -> CandidateRecord:
        candidate = self._session.scalar(select(CandidateRecord).where(CandidateRecord.user_id == str(user.id)))
        if candidate:
            return candidate

        candidate = CandidateRecord(
            user_id=str(user.id),
            name=user.name or user.email.split("@", 1)[0],
            preferences={},
        )
        self._session.add(candidate)
        self._session.commit()
        self._session.refresh(candidate)
        return candidate

    def update_for_user(
        self,
        user: User,
        *,
        name: str | None = None,
        headline: str | None = None,
        summary: str | None = None,
        location: str | None = None,
        preferences: dict | None = None,
    ) -> CandidateRecord:
        candidate = self.get_or_create_for_user(user)
        if name is not None:
            candidate.name = name
        if headline is not None:
            candidate.headline = headline
        if summary is not None:
            candidate.summary = summary
        if location is not None:
            candidate.location = location
        if preferences is not None:
            candidate.preferences = preferences
        self._session.commit()
        self._session.refresh(candidate)
        return candidate

    def create_evidence(
        self,
        candidate_id: UUID | str,
        *,
        source_type: str,
        title: str,
        content: str | None,
        external_url: str | None,
        metadata: dict,
    ) -> EvidenceRecord:
        evidence = EvidenceRecord(
            candidate_id=str(candidate_id),
            source_type=source_type,
            title=title,
            content=content,
            external_url=external_url,
            metadata_json=metadata,
            confidence=0.0,
            verification_status="CLAIMED",
        )
        self._session.add(evidence)
        self._session.commit()
        self._session.refresh(evidence)
        return evidence
