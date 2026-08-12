from uuid import UUID

from pydantic import BaseModel, Field


class CandidateAnalysisResponse(BaseModel):
    analysis_id: UUID
    status: str = "completed"
    capabilities: list[dict] = Field(default_factory=list)


class JobAnalysisRequest(BaseModel):
    job_description: str = Field(min_length=1, max_length=20000)
    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)


class JobAnalysisResponse(BaseModel):
    job_id: UUID
    requirements: list[dict] = Field(default_factory=list)


class MatchRequest(BaseModel):
    job_id: UUID


class MatchResponse(BaseModel):
    analysis_id: UUID
    match_score: int
    readiness_score: int
    strengths: list[dict] = Field(default_factory=list)
    gaps: list[dict] = Field(default_factory=list)
    recommendations: list = Field(default_factory=list)
    evidence_summary: list = Field(default_factory=list)
