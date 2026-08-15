from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.database.session import Base, init_database


JsonType = JSON().with_variant(JSONB, "postgresql")


class ProfileAnalysisSnapshotRecord(Base):
    """Integration-owned normalized profile snapshot linked to Platform candidate data."""

    __tablename__ = "integration_profile_analysis_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidates.id"), index=True, nullable=False
    )
    source_evidence_ids: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    profile_context: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ProfileAnalysisSnapshotRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        analysis_id: str,
        candidate_id: str,
        source_evidence_ids: list[str],
        profile_context: dict,
    ) -> ProfileAnalysisSnapshotRecord:
        record = ProfileAnalysisSnapshotRecord(
            id=analysis_id,
            candidate_id=candidate_id,
            source_evidence_ids=source_evidence_ids,
            profile_context=profile_context,
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record


def reset_profile_analysis_snapshots() -> None:
    init_database()
    from sqlalchemy import delete

    with _session_local() as session:
        session.execute(delete(ProfileAnalysisSnapshotRecord))
        session.commit()


def _session_local():
    from app.database.session import SessionLocal

    return SessionLocal()
