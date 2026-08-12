from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import CapabilityRecord, JobRecord, JobRequirementRecord


@dataclass(frozen=True)
class DemoJobSeed:
    title: str
    company: str
    location: str | None
    description: str
    source: str
    requirements: list[tuple[str, float, str]]


DEMO_JOBS: list[DemoJobSeed] = [
    DemoJobSeed(
        title="Backend Developer",
        company="Example Inc",
        location="Remote",
        description="Build FastAPI services with PostgreSQL, Redis, Docker, and pytest.",
        source="demo-provider",
        requirements=[
            ("Python", 90.0, "Evidence showing practical Python experience"),
            ("FastAPI", 90.0, "Evidence showing practical FastAPI experience"),
            ("PostgreSQL", 85.0, "Evidence showing practical PostgreSQL experience"),
            ("Redis", 70.0, "Evidence showing practical Redis experience"),
            ("Docker", 70.0, "Evidence showing practical Docker experience"),
            ("Testing", 75.0, "Evidence showing practical pytest/testing experience"),
        ],
    ),
    DemoJobSeed(
        title="Full Stack Engineer",
        company="Acme Labs",
        location="Lahore",
        description="Work across Next.js, FastAPI, and PostgreSQL to ship product features.",
        source="demo-provider",
        requirements=[
            ("React", 85.0, "Evidence showing practical React or Next.js experience"),
            ("FastAPI", 80.0, "Evidence showing backend API delivery"),
            ("PostgreSQL", 75.0, "Evidence showing database design experience"),
        ],
    ),
    DemoJobSeed(
        title="Platform Engineer",
        company="ByteWorks",
        location="Remote",
        description="Operate backend infrastructure with Python, Kubernetes, Docker, and Redis.",
        source="demo-provider",
        requirements=[
            ("Python", 90.0, "Evidence showing Python systems experience"),
            ("Docker", 80.0, "Evidence showing containerization experience"),
            ("Kubernetes", 90.0, "Evidence showing Kubernetes or orchestration experience"),
            ("Redis", 75.0, "Evidence showing Redis caching or session experience"),
        ],
    ),
]


class JobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def seed_demo_jobs(self) -> None:
        if self._session.scalar(select(func.count(JobRecord.id))) or 0:
            return

        for seed in DEMO_JOBS:
            job = JobRecord(
                id=str(uuid4()),
                title=seed.title,
                company=seed.company,
                location=seed.location,
                description=seed.description,
                source=seed.source,
                source_url=None,
                responsibilities=[],
                metadata_json={"provider": seed.source},
            )
            self._session.add(job)
            self._session.flush()
            for skill_name, importance, evidence_expectation in seed.requirements:
                self._session.add(
                    JobRequirementRecord(
                        id=str(uuid4()),
                        job_id=job.id,
                        skill_name=skill_name,
                        importance=importance,
                        requirement_type="REQUIRED",
                        evidence_expectation=evidence_expectation,
                        metadata_json={},
                    )
                )
        self._session.commit()

    def list_jobs(
        self,
        *,
        page: int,
        limit: int,
        source: str | None = None,
        query: str | None = None,
        location: str | None = None,
    ) -> tuple[list[JobRecord], int]:
        self.seed_demo_jobs()
        statement = select(JobRecord)
        if source:
            statement = statement.where(JobRecord.source == source)
        if query:
            q = f"%{query.lower()}%"
            statement = statement.where(
                func.lower(JobRecord.title).like(q) | func.lower(JobRecord.company).like(q) | func.lower(JobRecord.description).like(q)
            )
        if location:
            q = f"%{location.lower()}%"
            statement = statement.where(func.lower(func.coalesce(JobRecord.location, "")).like(q))
        total = self._session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        jobs = list(self._session.scalars(statement.order_by(JobRecord.created_at.desc()).offset((page - 1) * limit).limit(limit)))
        return jobs, int(total)

    def get_job(self, job_id: str) -> JobRecord | None:
        self.seed_demo_jobs()
        return self._session.get(JobRecord, job_id)

    def get_requirements(self, job_id: str) -> list[JobRequirementRecord]:
        return list(self._session.scalars(select(JobRequirementRecord).where(JobRequirementRecord.job_id == job_id)))

