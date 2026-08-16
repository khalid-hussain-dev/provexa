from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database.session import Base, init_database
from app.database.models import UuidType


class CourseIntegrationContextRecord(Base):
    __tablename__ = "integration_course_contexts"

    course_id: Mapped[str] = mapped_column(UuidType, ForeignKey("courses.id"), primary_key=True)
    interview_id: Mapped[str] = mapped_column(UuidType, ForeignKey("interviews.id"), nullable=False)
    evaluation_id: Mapped[str] = mapped_column(
        UuidType, ForeignKey("integration_interview_evaluations.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class LearningIntegrationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_course_context(
        self, *, course_id: str, interview_id: str, evaluation_id: str
    ) -> CourseIntegrationContextRecord:
        record = CourseIntegrationContextRecord(
            course_id=course_id, interview_id=interview_id, evaluation_id=evaluation_id
        )
        self._session.add(record)
        return record


def reset_learning_integration_records() -> None:
    init_database()
    from app.database.session import SessionLocal
    from sqlalchemy import delete

    with SessionLocal() as session:
        session.execute(delete(CourseIntegrationContextRecord))
        session.commit()
