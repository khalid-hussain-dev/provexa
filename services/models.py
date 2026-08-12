from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class CandidateProfile(BaseModel):
    name: str
    email: str
    resume_text: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    experience_years: float = 0
    skills: List[str] = []
    target_role: str
    additional_info: Optional[str] = None


class InterviewQuestion(BaseModel):
    question: str
    category: str
    difficulty: str


class InterviewResponse(BaseModel):
    question_id: str
    answer: str
    confidence: int = Field(default=5, ge=1, le=10)


class SkillAssessment(BaseModel):
    skill_name: str
    percentage: float = Field(ge=0, le=100)
    strength_level: str  # "expert", "advanced", "intermediate", "beginner", "novice"
    evidence: List[str] = []


class StrengthWeaknessAnalysis(BaseModel):
    strengths: List[str] = []
    weaknesses: List[str] = []
    improvement_areas: List[str] = []


class CourseRecommendation(BaseModel):
    title: str
    description: str
    duration_weeks: int
    topics: List[str] = []
    resources: List[str] = []
    priority: str  # "high", "medium", "low"


class CourseModule(BaseModel):
    module_title: str
    skill_name: str
    concept_explanation: str
    code_example: str
    validation_exercise: str
    solution_hint: Optional[str] = None


class DetailedCourse(BaseModel):
    title: str
    target_role: str
    current_score: float
    target_score: float
    selected_priority_skills: List[str] = []
    modules: List[CourseModule] = []
    summary: str


class ResumeOptimizationRequest(BaseModel):
    resume_text: str
    newly_learned_skills: List[str]


class ResumeOptimizationResult(BaseModel):
    original_resume_text: str
    updated_resume_text: str
    injected_skills: List[str] = []
    summary_of_changes: str


class InterviewResult(BaseModel):
    candidate_name: str
    target_role: str
    overall_score: float
    assessed_level: str = "junior"   # "fresher", "junior", "mid", "senior" — set by AI eval
    skill_assessments: List[SkillAssessment] = []
    analysis: StrengthWeaknessAnalysis
    course_recommendations: List[CourseRecommendation] = []
    detailed_course: Optional[DetailedCourse] = None
    interview_summary: str
    role_match_percentage: float = 0.0   # How well candidate matches their desired role
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class JobRecommendation(BaseModel):
    job_title: str
    company: str
    description: str
    required_skills: List[str]
    match_percentage: float
    salary_range: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    listing_type: str = "job"   # "job" or "internship"


class FinalAssessment(BaseModel):
    interview_result: InterviewResult
    job_recommendations: List[JobRecommendation] = []
    career_path_suggestions: List[str] = []


class SkillGap(BaseModel):
    """Represents a skill the candidate is weak in relative to their target role."""
    skill_name: str
    current_level: str          # "none", "beginner", "intermediate"
    required_level: str         # level needed for their target role
    importance_for_role: str    # "critical", "important", "nice-to-have"
    evidence: List[str] = []    # specific interview answers that showed the gap

