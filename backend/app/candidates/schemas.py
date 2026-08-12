from uuid import UUID

from pydantic import BaseModel, Field, field_validator

SOURCE_TYPES = {"CV", "GITHUB", "PORTFOLIO", "INTERVIEW", "LEARNING", "OTHER"}


class CandidateResponse(BaseModel):
    id: UUID
    name: str
    headline: str | None = None
    summary: str | None = None
    location: str | None = None
    preferences: dict = Field(default_factory=dict)


class CandidateUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    headline: str | None = Field(default=None, max_length=255)
    summary: str | None = Field(default=None, max_length=4000)
    location: str | None = Field(default=None, max_length=255)
    preferences: dict | None = None

    @field_validator("name", "headline", "summary", "location")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class EvidenceCreateRequest(BaseModel):
    source_type: str
    title: str = Field(min_length=1, max_length=255)
    content: str | None = Field(default=None, max_length=20000)
    external_url: str | None = Field(default=None, max_length=2048)
    metadata: dict = Field(default_factory=dict)

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        source_type = value.strip().upper()
        if source_type not in SOURCE_TYPES:
            raise ValueError(f"source_type must be one of {sorted(SOURCE_TYPES)}")
        return source_type

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return value.strip()


class EvidenceStoredResponse(BaseModel):
    evidence_id: UUID
    status: str = "stored"
