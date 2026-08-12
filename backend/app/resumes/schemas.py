from uuid import UUID

from pydantic import BaseModel, Field


class ResumeTemplateResponse(BaseModel):
    id: str
    name: str
    preview: dict | None = None


class ResumeTemplatesResponse(BaseModel):
    templates: list[ResumeTemplateResponse] = Field(default_factory=list)


class ResumeGenerateRequest(BaseModel):
    job_id: UUID
    template: str = Field(default="minimal")


class ResumeGenerateResponse(BaseModel):
    resume_id: UUID
    version: int
    content: dict
    evidence_references: list[str] = Field(default_factory=list)
