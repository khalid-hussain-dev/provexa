from uuid import UUID

from pydantic import BaseModel, Field


class CourseGenerateRequest(BaseModel):
    job_id: UUID
    interview_id: UUID


class CourseModuleResponse(BaseModel):
    module_id: UUID
    sequence: int
    title: str
    objective: str
    content: dict
    challenge: dict


class CourseGenerateResponse(BaseModel):
    course_id: UUID
    status: str = "GENERATED"
    title: str
    estimated_duration: str
    modules: list[CourseModuleResponse] = Field(default_factory=list)


class CourseDetailResponse(BaseModel):
    course_id: UUID
    status: str
    title: str
    objective: str
    estimated_duration: str
    modules: list[CourseModuleResponse] = Field(default_factory=list)
    progress: list[dict] = Field(default_factory=list)


class CourseProgressRequest(BaseModel):
    module_id: UUID
    completion_percent: float = Field(ge=0, le=100)
    assessment_score: float | None = Field(default=None, ge=0, le=100)
