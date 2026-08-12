from profile_analysis_crew import ProfileAnalysisCrew
from interview_crew import InterviewCrew
from course_crew import CourseGeneratorCrew
from models import (
    CandidateProfile, InterviewQuestion, InterviewResponse, 
    SkillAssessment, StrengthWeaknessAnalysis, CourseRecommendation, InterviewResult,
    DetailedCourse, ResumeOptimizationResult
)
from profile_analyzer import ProfileAnalyzer
from typing import List, Dict
import json


class InterviewSystem:
    def __init__(self):
        self.profile_analysis_crew = ProfileAnalysisCrew()
        self.interview_crew = InterviewCrew()
        self.course_generator_crew = CourseGeneratorCrew()
        self.profile_analyzer = ProfileAnalyzer()
        
    async def prepare_candidate_profile(self, candidate: CandidateProfile) -> Dict:
        """Prepare comprehensive candidate profile using ProfileAnalysisCrew"""
        # Extract resume text if provided
        resume_text = None
        if candidate.resume_text:
            if candidate.resume_text.endswith(('.pdf', '.docx')):
                resume_text = self.profile_analyzer.extract_resume_text(candidate.resume_text)
            else:
                resume_text = candidate.resume_text
        
        # Analyze GitHub profile if provided
        github_data = None
        if candidate.github_url:
            github_data = self.profile_analyzer.analyze_github_profile(candidate.github_url)
        
        # Analyze LinkedIn / Portfolio web profile if provided
        web_profile_data = None
        target_web_url = candidate.portfolio_url or candidate.linkedin_url
        if target_web_url:
            web_profile_data = self.profile_analyzer.analyze_web_profile(target_web_url)

        # Use ProfileAnalysisCrew to analyze the profile (async)
        profile_context = await self.profile_analysis_crew.analyze_profile(
            resume_text=resume_text,
            github_data=github_data,
            provided_skills=candidate.skills,
            experience_years=candidate.experience_years,
            target_role=candidate.target_role,
            linkedin_url=candidate.linkedin_url,
            portfolio_url=candidate.portfolio_url,
            web_profile_data=web_profile_data
        )
        
        # Add basic candidate info
        profile_context["name"] = candidate.name
        profile_context["email"] = candidate.email
        profile_context["additional_info"] = candidate.additional_info
        profile_context["linkedin_url"] = candidate.linkedin_url
        profile_context["portfolio_url"] = candidate.portfolio_url
        profile_context["resume_text"] = resume_text
        
        return profile_context

    
    async def generate_interview_questions(self, profile_context: Dict, num_questions: int = 10) -> List[InterviewQuestion]:
        """Generate interview questions using InterviewCrew based on profile context"""
        # Use InterviewCrew to generate domain-specific questions (async)
        questions_data = await self.interview_crew.generate_interview_questions(
            profile_context=profile_context,
            num_questions=num_questions
        )
        
        # Convert to InterviewQuestion objects
        questions = [
            InterviewQuestion(
                question=q.get("question", ""),
                category=q.get("category", "general"),
                difficulty=q.get("difficulty", "medium")
            )
            for q in questions_data.get("questions", [])
        ]
        
        return questions if questions else self._generate_fallback_questions(profile_context, num_questions)
    
    def _generate_fallback_questions(self, profile_context: Dict, num_questions: int) -> List[InterviewQuestion]:
        """Generate fallback questions if AI generation fails"""
        domain = profile_context.get('primary_domain', 'Software Engineer')
        skills = profile_context.get('all_skills', ['general programming'])
        
        questions = []
        for i in range(num_questions):
            skill = skills[i % len(skills)]
            questions.append(InterviewQuestion(
                question=f"Explain your experience with {skill} and how you've used it in your projects.",
                category=skill,
                difficulty="medium"
            ))
        
        return questions
    
    async def evaluate_interview_responses(
        self, 
        profile_context: Dict, 
        questions: List[InterviewQuestion], 
        responses: List[InterviewResponse]
    ) -> InterviewResult:
        """Evaluate interview responses using InterviewCrew and generate comprehensive assessment"""
        
        # Convert questions and responses to dict format for InterviewCrew
        questions_dict = [
            {
                "question": q.question,
                "category": q.category,
                "difficulty": q.difficulty
            }
            for q in questions
        ]
        
        responses_dict = [
            {
                "answer": r.answer,
                "confidence": r.confidence
            }
            for r in responses
        ]
        
        # Use InterviewCrew to evaluate (async)
        evaluation_result = await self.interview_crew.evaluate_interview(
            profile_context=profile_context,
            questions=questions_dict,
            responses=responses_dict
        )
        
        # Parse results and create InterviewResult
        return self._parse_evaluation_result(evaluation_result, profile_context)
    
    def _parse_evaluation_result(
        self, 
        evaluation_result: Dict, 
        profile_context: Dict
    ) -> InterviewResult:
        """Parse the evaluation result from InterviewCrew and create InterviewResult object"""
        try:
            # Extract skill assessments
            skill_assessments = [
                SkillAssessment(
                    skill_name=s.get("skill_name", ""),
                    percentage=float(s.get("percentage", 0)),
                    strength_level=s.get("proficiency_level", "beginner"),
                    evidence=s.get("evidence", [])
                )
                for s in evaluation_result.get("skill_assessments", [])
            ]
            
            # Extract strong and weak areas
            strong_areas = evaluation_result.get("strong_areas", [])
            weak_areas   = evaluation_result.get("weak_areas", [])
            
            strengths        = [area.get("area", "") for area in strong_areas]
            weaknesses       = [area.get("area", "") for area in weak_areas]
            improvement_areas = evaluation_result.get("borderline_areas", [])
            
            analysis = StrengthWeaknessAnalysis(
                strengths=strengths,
                weaknesses=weaknesses,
                improvement_areas=improvement_areas
            )
            
            # Generate course recommendations based on weak areas
            course_recommendations = self._generate_course_recommendations(weak_areas, profile_context)
            
            # Generate interview summary
            interview_summary = self._generate_interview_summary(
                evaluation_result, profile_context
            )

            # ── AI-assessed level (drives job matching, not experience years) ──
            # The evaluation crew should return "domain_readiness" as one of:
            # "fresher", "junior", "mid", "senior"
            raw_readiness = evaluation_result.get("domain_readiness", "junior").lower()
            level_map = {
                "not_ready": "fresher", "needs_improvement": "fresher",
                "beginner": "fresher",
                "junior": "junior", "entry": "junior",
                "mid": "mid", "intermediate": "mid",
                "senior": "senior", "expert": "senior", "advanced": "senior",
            }
            assessed_level = level_map.get(raw_readiness, "junior")

            # Role match: how well the candidate fits their desired role (0–100)
            overall_score = float(evaluation_result.get("overall_domain_score", 50))
            role_match_percentage = float(
                evaluation_result.get("role_match_percentage", overall_score)
            )
            
            return InterviewResult(
                candidate_name=profile_context.get("name", "Unknown"),
                target_role=profile_context.get("primary_domain", profile_context.get("target_role", "Unknown")),
                overall_score=overall_score,
                assessed_level=assessed_level,
                role_match_percentage=role_match_percentage,
                skill_assessments=skill_assessments,
                analysis=analysis,
                course_recommendations=course_recommendations,
                interview_summary=interview_summary
            )
        except Exception as e:
            # Fallback if parsing fails
            return InterviewResult(
                candidate_name=profile_context.get("name", "Unknown"),
                target_role=profile_context.get("primary_domain", "Unknown"),
                overall_score=50.0,
                assessed_level="junior",
                role_match_percentage=50.0,
                skill_assessments=[],
                analysis=StrengthWeaknessAnalysis(),
                course_recommendations=[],
                interview_summary=str(evaluation_result)
            )
    
    async def generate_targeted_course(
        self,
        target_role: str,
        current_score: float,
        weaknesses: List[str],
        improvement_areas: List[str] = None
    ) -> DetailedCourse:
        """Generate targeted crash course with Strategic Learning Director and Technical Course Creator"""
        return await self.course_generator_crew.generate_targeted_course(
            target_role=target_role,
            current_score=current_score,
            all_weaknesses=weaknesses,
            improvement_areas=improvement_areas
        )

    async def optimize_resume(
        self,
        resume_text: str,
        newly_learned_skills: List[str]
    ) -> ResumeOptimizationResult:
        """Optimize CV text with ATS Resume Optimizer agent"""
        return await self.course_generator_crew.optimize_resume(
            resume_text=resume_text,
            newly_learned_skills=newly_learned_skills
        )

    def _generate_course_recommendations(self, weak_areas: List[Dict], profile_context: Dict) -> List[CourseRecommendation]:
        """Generate course recommendations based on weak areas"""
        courses = []
        
        for area in weak_areas[:5]:  # Limit to top 5 weak areas
            area_name = area.get("area", "General Skills")
            improvement = area.get("improvement_needed", "Improve skills in this area")
            
            courses.append(CourseRecommendation(
                title=f"Advanced {area_name}",
                description=f"Comprehensive course to {improvement}",
                duration_weeks=4,
                topics=[area_name, "Best Practices", "Advanced Techniques"],
                resources=["Online tutorials", "Documentation", "Practice projects"],
                priority="high"
            ))
        
        return courses
    
    def _generate_interview_summary(self, evaluation_result: Dict, profile_context: Dict) -> str:
        """Generate a natural language interview summary"""
        domain = profile_context.get("primary_domain", "Software Engineering")
        score = evaluation_result.get("overall_domain_score", 50)
        readiness = evaluation_result.get("domain_readiness", "needs_improvement")
        
        strong_areas = evaluation_result.get("strong_areas", [])
        weak_areas = evaluation_result.get("weak_areas", [])
        
        summary = f"Interview Assessment for {domain} Role\n\n"
        summary += f"Overall Score: {score}/100\n"
        summary += f"Domain Readiness: {readiness}\n\n"
        
        if strong_areas:
            summary += "Strong Areas:\n"
            for area in strong_areas[:3]:
                summary += f"- {area.get('area', 'N/A')}\n"
            summary += "\n"
        
        if weak_areas:
            summary += "Areas for Improvement:\n"
            for area in weak_areas[:3]:
                summary += f"- {area.get('area', 'N/A')}\n"
            summary += "\n"
        
        summary += "The candidate demonstrates potential in the " + domain + " domain. "
        summary += "Focus on addressing the identified weak areas through recommended courses."
        
        return summary

