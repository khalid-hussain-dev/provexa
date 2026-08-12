from uuid import UUID

from pydantic import BaseModel, Field


class JobRequirementResponse(BaseModel):
    id: UUID
    skill_name: str
    importance: int
    requirement_type: str
    evidence_expectation: str | None = None


class JobSummaryResponse(BaseModel):
    job_id: UUID
    title: str
    company: str
    location: str | None = None
    source: str


class JobDetailResponse(BaseModel):
    job_id: UUID
    title: str
    company: str
    location: str | None = None
    description: str
    seniority: str | None = None
    source: str
    source_url: str | None = None
    responsibilities: list = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    requirements: list[JobRequirementResponse] = Field(default_factory=list)


class JobListResponse(BaseModel):
    jobs: list[JobSummaryResponse] = Field(default_factory=list)
    page: int
    limit: int
    total: int


class JobRecommendRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=20)
    location: str | None = None


class JobRecommendationResponse(BaseModel):
    job_id: UUID
    title: str
    company: str
    match_score: int
    readiness_score: int
    source: str


class JobRecommendResponse(BaseModel):
    jobs: list[JobRecommendationResponse] = Field(default_factory=list)
