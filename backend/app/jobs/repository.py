from dataclasses import dataclass
import re
from uuid import uuid4

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
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
        self.sync_adzuna_jobs(query=query, location=location, limit=max(limit, 20))
        statement = self._build_statement(source=source, query=query, location=location)
        total = self._session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        jobs = list(self._session.scalars(statement.order_by(JobRecord.created_at.desc()).offset((page - 1) * limit).limit(limit)))
        if not jobs and (query or location):
            statement = self._build_statement(source=source, query=None, location=None)
            total = self._session.scalar(select(func.count()).select_from(statement.subquery())) or 0
            jobs = list(self._session.scalars(statement.order_by(JobRecord.created_at.desc()).offset((page - 1) * limit).limit(limit)))
        return jobs, int(total)

    def _build_statement(self, *, source: str | None, query: str | None, location: str | None):
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
        return statement

    def sync_adzuna_jobs(self, *, query: str | None, location: str | None, limit: int) -> None:
        settings = get_settings()
        if not settings.adzuna_app_id or not settings.job_api_key:
            return

        url = f"https://api.adzuna.com/v1/api/jobs/{settings.adzuna_country}/search/1"
        inserted = False
        search_variants = _adzuna_search_variants(query=query, location=location)

        try:
            with httpx.Client(timeout=12) as client:
                for search_query, search_location in search_variants:
                    params = {
                        "app_id": settings.adzuna_app_id,
                        "app_key": settings.job_api_key,
                        "what": search_query,
                        "results_per_page": min(max(limit, 1), 50),
                        "content-type": "application/json",
                    }
                    if search_location:
                        params["where"] = search_location

                    response = client.get(url, params=params)
                    response.raise_for_status()
                    results = response.json().get("results", [])
                    for item in results:
                        source_url = item.get("redirect_url")
                        if not source_url or self._session.scalar(select(JobRecord.id).where(JobRecord.source_url == source_url)):
                            continue
                        job = JobRecord(
                            id=str(uuid4()),
                            title=(item.get("title") or search_query)[:255],
                            company=(item.get("company") or {}).get("display_name", "Adzuna listing")[:255],
                            location=(item.get("location") or {}).get("display_name"),
                            description=_clean_text(item.get("description") or "No description provided."),
                            seniority=None,
                            source="adzuna",
                            source_url=source_url,
                            responsibilities=[],
                            metadata_json={
                                "provider": "adzuna",
                                "category": (item.get("category") or {}).get("label"),
                                "contract_type": item.get("contract_type"),
                                "salary_min": item.get("salary_min"),
                                "salary_max": item.get("salary_max"),
                                "search_query": search_query,
                                "search_location": search_location,
                            },
                        )
                        self._session.add(job)
                        self._session.flush()
                        for skill_name in _infer_skills(job.title, job.description):
                            self._session.add(
                                JobRequirementRecord(
                                    id=str(uuid4()),
                                    job_id=job.id,
                                    skill_name=skill_name,
                                    importance=75.0,
                                    requirement_type="INFERRED",
                                    evidence_expectation=f"Evidence showing practical {skill_name} experience",
                                    metadata_json={"provider": "adzuna"},
                                )
                            )
                        inserted = True
                    if inserted:
                        self._session.commit()
                        return
        except Exception:
            return

    def get_job(self, job_id: str) -> JobRecord | None:
        self.seed_demo_jobs()
        return self._session.get(JobRecord, job_id)

    def get_requirements(self, job_id: str) -> list[JobRequirementRecord]:
        return list(self._session.scalars(select(JobRequirementRecord).where(JobRequirementRecord.job_id == job_id)))


def _clean_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:4000]


def _infer_skills(title: str, description: str) -> list[str]:
    text = f"{title} {description}".lower()
    skills = [
        "Python",
        "JavaScript",
        "TypeScript",
        "React",
        "Node.js",
        "FastAPI",
        "Django",
        "PostgreSQL",
        "SQL",
        "Redis",
        "Docker",
        "Kubernetes",
        "AWS",
        "Azure",
        "Git",
        "Testing",
        "REST APIs",
    ]
    found = [skill for skill in skills if skill.lower().replace(".", "") in text.replace(".", "")]
    return found[:6] or ["Communication", "Problem Solving", "Delivery"]


def _adzuna_search_variants(*, query: str | None, location: str | None) -> list[tuple[str, str | None]]:
    normalized_query = (query or "").strip()
    normalized_location = (location or "").strip() or None
    role_variants = _role_variants(normalized_query)
    search_terms = [normalized_query] if normalized_query else []
    for variant in role_variants:
        if variant not in search_terms:
            search_terms.append(variant)
    if not search_terms:
        search_terms = ["software engineer", "developer", "engineer"]

    variants: list[tuple[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()
    for term in search_terms:
        for candidate_location in (normalized_location, None):
            pair = (term, candidate_location)
            if pair not in seen:
                seen.add(pair)
                variants.append(pair)
    return variants


def _role_variants(query: str) -> list[str]:
    lowered = query.lower()
    variants: list[str] = []
    if "mobile" in lowered:
        variants.extend(["Mobile Developer", "Android Developer", "iOS Developer", "Mobile App Developer"])
    if "backend" in lowered:
        variants.extend(["Backend Developer", "Python Developer", "API Engineer"])
    if "frontend" in lowered or "front end" in lowered:
        variants.extend(["Frontend Developer", "React Developer", "UI Engineer"])
    if "full stack" in lowered or "fullstack" in lowered:
        variants.extend(["Full Stack Developer", "Full Stack Engineer", "Web Developer"])
    if "data" in lowered:
        variants.extend(["Data Engineer", "Data Analyst", "Machine Learning Engineer"])
    if "devops" in lowered or "platform" in lowered or "infrastructure" in lowered:
        variants.extend(["DevOps Engineer", "Platform Engineer", "Site Reliability Engineer"])
    if "product" in lowered:
        variants.extend(["Product Manager", "Technical Product Manager"])
    if not variants:
        variants.extend(["software engineer", "developer", "engineer"])
    return variants
