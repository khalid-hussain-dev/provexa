from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import aiofiles
import os
import json
from datetime import datetime

from models import (
    CandidateProfile, InterviewQuestion, InterviewResponse, 
    InterviewResult, JobRecommendation, FinalAssessment
)
from interview_system import InterviewSystem
from job_service import JobRecommendationService
from utils import parse_crew_result


def safe_parse_list(value: Optional[str]) -> list:
    """Parse a skills/tags string into a list.
    Accepts: JSON array '["a","b"]', comma-separated 'a,b', or empty/None."""
    if not value or not value.strip():
        return []
    text = value.strip()
    if text.startswith("["):
        try:
            result = json.loads(text)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError:
            pass
    # Fallback: treat as comma-separated
    return [s.strip() for s in text.split(",") if s.strip()]


def safe_parse_json(value: str) -> any:
    """Parse a JSON string, raising HTTPException(422) with a clear message on failure."""
    if not value or not value.strip():
        raise HTTPException(status_code=422, detail="'responses' field is required and must be valid JSON")
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid JSON in 'responses': {exc}"
        )

app = FastAPI(title="AI Interview & Assessment System", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
interview_system = InterviewSystem()
job_service = JobRecommendationService()

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Interview & Assessment System",
        "version": "1.0.0"
    }


@app.post("/api/v1/profile/analyze")
async def analyze_profile(
    name: str = Form(...),
    email: str = Form(...),
    target_role: str = Form(...),
    experience_years: float = Form(0.0),
    github_url: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    portfolio_url: Optional[str] = Form(None),
    additional_info: Optional[str] = Form(None),
    resume: Optional[UploadFile] = None,
    skills: Optional[str] = Form(None)  # JSON string of skills array
):
    """
    Analyze candidate profile (resume + GitHub + LinkedIn + Portfolio) using ProfileAnalysisCrew.
    Returns domain classification, extracted skills, and comprehensive profile context.
    This is the first step before generating interview questions.
    """
    try:
        # Handle resume upload
        resume_text = None
        if resume:
            file_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{resume.filename}")
            async with aiofiles.open(file_path, 'wb') as f:
                content = await resume.read()
                await f.write(content)
            resume_text = file_path
        
        # Parse skills if provided
        skills_list = safe_parse_list(skills)
        
        # Create candidate profile
        candidate = CandidateProfile(
            name=name,
            email=email,
            target_role=target_role,
            experience_years=experience_years,
            github_url=github_url,
            linkedin_url=linkedin_url,
            portfolio_url=portfolio_url,
            additional_info=additional_info,
            resume_text=resume_text,
            skills=skills_list
        )

        
        # Prepare profile using ProfileAnalysisCrew
        profile_context = await interview_system.prepare_candidate_profile(candidate)
        
        return {
            "status": "success",
            "profile_context": {
                "name": profile_context.get("name"),
                "primary_domain": profile_context.get("primary_domain"),
                "secondary_domains": profile_context.get("secondary_domains"),
                "domain_confidence": profile_context.get("domain_confidence"),
                "all_skills": profile_context.get("all_skills"),
                "skill_clusters": profile_context.get("skill_clusters"),
                "technical_strengths": profile_context.get("technical_strengths"),
                "potential_weaknesses": profile_context.get("potential_weaknesses"),
                "interview_readiness": profile_context.get("interview_readiness"),
                "recommended_interview_depth": profile_context.get("recommended_interview_depth"),
                "candidate_summary": profile_context.get("candidate_summary"),
                "profile_context": profile_context.get("profile_context")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/interview/questions")
async def generate_interview_questions(
    name: str = Form(...),
    email: str = Form(...),
    target_role: str = Form(...),
    experience_years: float = Form(0.0),
    github_url: Optional[str] = Form(None),
    additional_info: Optional[str] = Form(None),
    resume: Optional[UploadFile] = None,
    skills: Optional[str] = Form(None),
    num_questions: int = Form(10)
):
    """
    Generate interview questions based on candidate profile.
    Returns a list of questions with categories and difficulty levels.
    """
    try:
        # Handle resume upload
        resume_text = None
        if resume:
            file_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{resume.filename}")
            async with aiofiles.open(file_path, 'wb') as f:
                content = await resume.read()
                await f.write(content)
            resume_text = file_path
        
        # Parse skills if provided
        skills_list = safe_parse_list(skills)
        
        # Create candidate profile
        candidate = CandidateProfile(
            name=name,
            email=email,
            target_role=target_role,
            experience_years=experience_years,
            github_url=github_url,
            additional_info=additional_info,
            resume_text=resume_text,
            skills=skills_list
        )
        
        # Prepare profile context using ProfileAnalysisCrew and generate questions using InterviewCrew
        profile_context = await interview_system.prepare_candidate_profile(candidate)
        questions = await interview_system.generate_interview_questions(profile_context, num_questions)
        
        return {
            "status": "success",
            "questions": [
                {
                    "id": str(i),
                    "question": q.question,
                    "category": q.category,
                    "difficulty": q.difficulty
                }
                for i, q in enumerate(questions)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/interview/evaluate")
async def evaluate_interview(
    name: str = Form(...),
    email: str = Form(...),
    target_role: str = Form(...),
    experience_years: float = Form(0.0),
    github_url: Optional[str] = Form(None),
    additional_info: Optional[str] = Form(None),
    resume: Optional[UploadFile] = None,
    skills: Optional[str] = Form(None),
    responses: str = Form(...)  # JSON string of interview responses
):
    """
    Evaluate interview responses and generate comprehensive assessment.
    Returns skill assessments with percentages, strengths, weaknesses, and course recommendations.
    """
    try:
        # Handle resume upload
        resume_text = None
        if resume:
            file_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{resume.filename}")
            async with aiofiles.open(file_path, 'wb') as f:
                content = await resume.read()
                await f.write(content)
            resume_text = file_path
        
        # Parse skills and responses
        skills_list = safe_parse_list(skills)
        responses_data = safe_parse_json(responses)
        
        # Create candidate profile
        candidate = CandidateProfile(
            name=name,
            email=email,
            target_role=target_role,
            experience_years=experience_years,
            github_url=github_url,
            additional_info=additional_info,
            resume_text=resume_text,
            skills=skills_list
        )
        
        # Prepare profile context using ProfileAnalysisCrew
        profile_context = await interview_system.prepare_candidate_profile(candidate)
        
        # Recreate questions and responses (in production, store questions from previous step)
        # For now, we'll use the responses directly
        questions = [
            InterviewQuestion(
                question=r.get("question", ""),
                category=r.get("category", "general"),
                difficulty=r.get("difficulty", "medium")
            )
            for r in responses_data
        ]
        
        interview_responses = [
            InterviewResponse(
                question_id=str(i),
                answer=r.get("answer", ""),
                confidence=r.get("confidence", 5)
            )
            for i, r in enumerate(responses_data)
        ]
        
        # Evaluate responses using InterviewCrew
        result = await interview_system.evaluate_interview_responses(
            profile_context, questions, interview_responses
        )
        
        return {
            "status": "success",
            "result": {
                "candidate_name": result.candidate_name,
                "target_role": result.target_role,
                "overall_score": result.overall_score,
                "skill_assessments": [
                    {
                        "skill_name": s.skill_name,
                        "percentage": s.percentage,
                        "strength_level": s.strength_level,
                        "evidence": s.evidence
                    }
                    for s in result.skill_assessments
                ],
                "analysis": {
                    "strengths": result.analysis.strengths,
                    "weaknesses": result.analysis.weaknesses,
                    "improvement_areas": result.analysis.improvement_areas
                },
                "course_recommendations": [
                    {
                        "title": c.title,
                        "description": c.description,
                        "duration_weeks": c.duration_weeks,
                        "topics": c.topics,
                        "resources": c.resources,
                        "priority": c.priority
                    }
                    for c in result.course_recommendations
                ],
                "interview_summary": result.interview_summary,
                "timestamp": result.timestamp.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/jobs/recommend")
async def recommend_jobs(
    interview_result: dict,
    location: Optional[str] = None,
    limit: int = 5
):
    """
    Recommend jobs based on interview assessment.
    Calls external job API or generates mock recommendations.
    """
    try:
        # Convert dict to InterviewResult
        from models import InterviewResult, SkillAssessment, StrengthWeaknessAnalysis, CourseRecommendation
        
        skill_assessments = [
            SkillAssessment(**s) for s in interview_result.get("skill_assessments", [])
        ]
        
        analysis = StrengthWeaknessAnalysis(
            strengths=interview_result.get("analysis", {}).get("strengths", []),
            weaknesses=interview_result.get("analysis", {}).get("weaknesses", []),
            improvement_areas=interview_result.get("analysis", {}).get("improvement_areas", [])
        )
        
        course_recommendations = [
            CourseRecommendation(**c) for c in interview_result.get("course_recommendations", [])
        ]
        
        result = InterviewResult(
            candidate_name=interview_result.get("candidate_name"),
            target_role=interview_result.get("target_role"),
            overall_score=interview_result.get("overall_score", 0),
            skill_assessments=skill_assessments,
            analysis=analysis,
            course_recommendations=course_recommendations,
            interview_summary=interview_result.get("interview_summary", "")
        )
        
        # Get job recommendations
        jobs = await job_service.recommend_jobs(result, location, limit)
        
        return {
            "status": "success",
            "jobs": [
                {
                    "job_title": j.job_title,
                    "company": j.company,
                    "description": j.description,
                    "required_skills": j.required_skills,
                    "match_percentage": j.match_percentage,
                    "salary_range": j.salary_range,
                    "location": j.location,
                    "url": j.url
                }
                for j in jobs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/assessment/complete")
async def complete_assessment(
    name: str = Form(...),
    email: str = Form(...),
    target_role: str = Form(...),
    experience_years: float = Form(0.0),
    github_url: Optional[str] = Form(None),
    additional_info: Optional[str] = Form(None),
    resume: Optional[UploadFile] = None,
    skills: Optional[str] = Form(None),
    responses: str = Form(...),
    location: Optional[str] = None,
    job_limit: int = 5
):
    """
    Complete end-to-end assessment:
    1. Analyze profile
    2. Evaluate interview responses
    3. Generate skill assessments
    4. Recommend courses
    5. Suggest jobs
    
    Returns comprehensive final assessment.
    """
    try:
        # Handle resume upload
        resume_text = None
        if resume:
            file_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{resume.filename}")
            async with aiofiles.open(file_path, 'wb') as f:
                content = await resume.read()
                await f.write(content)
            resume_text = file_path
        
        # Parse skills and responses
        skills_list = safe_parse_list(skills)
        responses_data = safe_parse_json(responses)
        
        # Create candidate profile
        candidate = CandidateProfile(
            name=name,
            email=email,
            target_role=target_role,
            experience_years=experience_years,
            github_url=github_url,
            additional_info=additional_info,
            resume_text=resume_text,
            skills=skills_list
        )
        
        # Prepare profile context using ProfileAnalysisCrew
        profile_context = await interview_system.prepare_candidate_profile(candidate)
        
        # Recreate questions and responses
        questions = [
            InterviewQuestion(
                question=r.get("question", ""),
                category=r.get("category", "general"),
                difficulty=r.get("difficulty", "medium")
            )
            for r in responses_data
        ]
        
        interview_responses = [
            InterviewResponse(
                question_id=str(i),
                answer=r.get("answer", ""),
                confidence=r.get("confidence", 5)
            )
            for i, r in enumerate(responses_data)
        ]
        
        # Evaluate interview using InterviewCrew
        interview_result = await interview_system.evaluate_interview_responses(
            profile_context, questions, interview_responses
        )
        
        # Get job recommendations
        jobs = await job_service.recommend_jobs(interview_result, location, job_limit)
        
        # Generate career path suggestions
        career_paths = []
        if interview_result.overall_score >= 80:
            career_paths.append(f"Senior {target_role}")
            career_paths.append(f"Tech Lead - {target_role}")
        elif interview_result.overall_score >= 60:
            career_paths.append(f"Mid-level {target_role}")
            career_paths.append(f"{target_role} Specialist")
        else:
            career_paths.append(f"Junior {target_role}")
            career_paths.append(f"{target_role} Intern")
        
        return {
            "status": "success",
            "assessment": {
                "interview_result": {
                    "candidate_name": interview_result.candidate_name,
                    "target_role": interview_result.target_role,
                    "overall_score": interview_result.overall_score,
                    "skill_assessments": [
                        {
                            "skill_name": s.skill_name,
                            "percentage": s.percentage,
                            "strength_level": s.strength_level,
                            "evidence": s.evidence
                        }
                        for s in interview_result.skill_assessments
                    ],
                    "analysis": {
                        "strengths": interview_result.analysis.strengths,
                        "weaknesses": interview_result.analysis.weaknesses,
                        "improvement_areas": interview_result.analysis.improvement_areas
                    },
                    "course_recommendations": [
                        {
                            "title": c.title,
                            "description": c.description,
                            "duration_weeks": c.duration_weeks,
                            "topics": c.topics,
                            "resources": c.resources,
                            "priority": c.priority
                        }
                        for c in interview_result.course_recommendations
                    ],
                    "interview_summary": interview_result.interview_summary
                },
                "job_recommendations": [
                    {
                        "job_title": j.job_title,
                        "company": j.company,
                        "description": j.description,
                        "required_skills": j.required_skills,
                        "match_percentage": j.match_percentage,
                        "salary_range": j.salary_range,
                        "location": j.location,
                        "url": j.url
                    }
                    for j in jobs
                ],
                "career_path_suggestions": career_paths
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/course/generate")
async def generate_targeted_course(
    target_role: str = Form(...),
    current_score: float = Form(50.0),
    weaknesses: Optional[str] = Form(None),
    improvement_areas: Optional[str] = Form(None)
):
    """
    Generate a targeted crash course using Strategic Learning Director & Technical Course Creator.
    Selects 2-3 priority skills and produces detailed modules with code examples & validation exercises.
    """
    try:
        weak_list = safe_parse_list(weaknesses)
        imp_list = safe_parse_list(improvement_areas)
        
        course = await interview_system.generate_targeted_course(
            target_role=target_role,
            current_score=current_score,
            weaknesses=weak_list,
            improvement_areas=imp_list
        )
        return {
            "status": "success",
            "course": course.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/resume/inject-skills")
async def inject_skills_into_resume(
    resume_text: str = Form(...),
    newly_learned_skills: str = Form(...)
):
    """
    ATS Resume Optimizer endpoint:
    Injects newly mastered course skills seamlessly into the candidate's existing resume text.
    """
    try:
        skills_list = safe_parse_list(newly_learned_skills)
        result = await interview_system.optimize_resume(
            resume_text=resume_text,
            newly_learned_skills=skills_list
        )
        return {
            "status": "success",
            "result": result.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
