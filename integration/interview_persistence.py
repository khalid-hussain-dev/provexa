from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, delete, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database.session import Base, init_database
from app.database.models import UuidType

JsonType = JSON().with_variant(JSONB, "postgresql")


class InterviewContextRecord(Base):
    __tablename__ = "integration_interview_contexts"

    interview_id: Mapped[str] = mapped_column(
        UuidType, ForeignKey("interviews.id"), primary_key=True
    )
    profile_snapshot_id: Mapped[str] = mapped_column(
        UuidType, ForeignKey("integration_profile_analysis_snapshots.id"), nullable=False
    )
    profile_context: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class InterviewEvaluationRecord(Base):
    __tablename__ = "integration_interview_evaluations"

    id: Mapped[str] = mapped_column(UuidType, primary_key=True)
    interview_id: Mapped[str] = mapped_column(
        UuidType, ForeignKey("interviews.id"), unique=True, index=True, nullable=False
    )
    profile_snapshot_id: Mapped[str] = mapped_column(
        UuidType, ForeignKey("integration_profile_analysis_snapshots.id"), nullable=False
    )
    result: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class InterviewIntegrationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_context(
        self,
        *,
        interview_id: str,
        profile_snapshot_id: str,
        profile_context: dict,
    ) -> InterviewContextRecord:
        record = InterviewContextRecord(
            interview_id=interview_id,
            profile_snapshot_id=profile_snapshot_id,
            profile_context=profile_context,
        )
        self._session.add(record)
        return record

    def get_context(self, interview_id: str) -> InterviewContextRecord | None:
        return self._session.get(InterviewContextRecord, interview_id)

    def get_evaluation(self, interview_id: str) -> InterviewEvaluationRecord | None:
        return self._session.scalar(
            select(InterviewEvaluationRecord).where(
                InterviewEvaluationRecord.interview_id == interview_id
            )
        )

    def create_evaluation(
        self,
        *,
        evaluation_id: str,
        interview_id: str,
        profile_snapshot_id: str,
        result: dict,
    ) -> InterviewEvaluationRecord:
        record = InterviewEvaluationRecord(
            id=evaluation_id,
            interview_id=interview_id,
            profile_snapshot_id=profile_snapshot_id,
            result=result,
        )
        self._session.add(record)
        return record


def reset_interview_integration_records() -> None:
    init_database()
    from app.database.session import SessionLocal

    with SessionLocal() as session:
        session.execute(delete(InterviewEvaluationRecord))
        session.execute(delete(InterviewContextRecord))
        session.commit()
