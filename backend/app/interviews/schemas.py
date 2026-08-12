from uuid import UUID

from pydantic import BaseModel, Field


class InterviewQuestionResponse(BaseModel):
    question_id: UUID
    question: str
    competency: str


class InterviewCreateRequest(BaseModel):
    job_id: UUID


class InterviewCreateResponse(BaseModel):
    interview_id: UUID
    status: str = "CREATED"
    first_question: InterviewQuestionResponse


class InterviewAnswerRequest(BaseModel):
    question_id: UUID
    answer: str = Field(min_length=1, max_length=10000)


class InterviewAnswerResponse(BaseModel):
    score: int
    feedback: str
    next_question: InterviewQuestionResponse | None = None


class InterviewCompleteResponse(BaseModel):
    overall_score: int
    technical_score: int
    communication_score: int
    problem_solving_score: int
    role_alignment_score: int
    verdict: str
    strengths: list[dict] = Field(default_factory=list)
    gaps: list[dict] = Field(default_factory=list)
    recommendations: list[dict] = Field(default_factory=list)

