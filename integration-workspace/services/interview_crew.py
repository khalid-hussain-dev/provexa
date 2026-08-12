from crewai import Agent, Task, Crew, LLM
from config import settings
from typing import Dict, List, Any
import json
from utils import parse_crew_result, get_default_llm


class InterviewCrew:
    """Crew dedicated to conducting interviews and identifying strong/weak areas"""
    
    def __init__(self):
        self.llm = get_default_llm(temperature=0.7)
    
    def get_domain_interviewer(self) -> Agent:
        """Agent to generate domain-specific interview questions"""
        return Agent(
            role="Domain-Specific Technical Interviewer",
            goal="Generate targeted interview questions based on the candidate's domain and profile context",
            backstory="""You are a senior technical interviewer specializing in conducting domain-specific 
            interviews. You understand the nuances of different technical domains (Backend, Frontend, DevOps, 
            Data Science, etc.) and can craft questions that accurately assess a candidate's capabilities 
            within their specific domain.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def get_response_evaluator(self) -> Agent:
        """Agent to evaluate interview responses and assess proficiency"""
        return Agent(
            role="Technical Response Evaluator",
            goal="Evaluate interview responses to determine skill proficiency and identify strong/weak areas",
            backstory="""You are an expert technical assessor who can accurately gauge a candidate's 
            proficiency based on their interview responses. You provide objective evaluations with 
            percentage scores and identify specific strengths and weaknesses within their domain.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def get_strength_weakness_analyzer(self) -> Agent:
        """Agent to analyze and categorize strengths and weaknesses"""
        return Agent(
            role="Strength and Weakness Analyzer",
            goal="Analyze interview performance to identify specific strong areas and weak areas with detailed explanations",
            backstory="""You are an expert technical analyst who specializes in identifying patterns in 
            candidate responses. You can distinguish between genuine strengths and areas that need improvement, 
            providing specific evidence and actionable insights.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def get_skill_assessor(self) -> Agent:
        """Agent to provide percentage-based skill assessments"""
        return Agent(
            role="Skill Proficiency Assessor",
            goal="Provide detailed skill assessments with percentage scores based on interview performance",
            backstory="""You are an expert technical assessor who can quantify a candidate's skill level 
            with precision. You provide percentage scores (0-100%) for each skill, backed by specific 
            evidence from their interview responses.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    async def generate_interview_questions(
        self, 
        profile_context: Dict, 
        num_questions: int = 10
    ) -> List[Dict]:
        """Generate domain-specific interview questions based on profile context"""
        
        domain_interviewer = self.get_domain_interviewer()
        
        # Build context string
        context_str = f"""
        CANDIDATE PROFILE CONTEXT:
        - Primary Domain: {profile_context.get('primary_domain', 'Unknown')}
        - Secondary Domains: {', '.join(profile_context.get('secondary_domains', []))}
        - All Skills: {', '.join(profile_context.get('all_skills', []))}
        - Technical Strengths: {', '.join(profile_context.get('technical_strengths', []))}
        - Potential Weaknesses: {', '.join(profile_context.get('potential_weaknesses', []))}
        - Interview Focus Areas: {', '.join(profile_context.get('interview_focus_areas', []))}
        - Recommended Depth: {profile_context.get('recommended_interview_depth', 'intermediate')}
        
        Profile Context:
        {profile_context.get('profile_context', '')}
        """
        
        questions_task = Task(
            description=f"""Generate {num_questions} domain-specific interview questions for a candidate in the {profile_context.get('primary_domain', 'Unknown')} domain.
            
            {context_str}
            
            Requirements:
            - Questions should be appropriate for the recommended interview depth
            - Cover both the primary domain and secondary domains
            - Include questions that test identified strengths to confirm them
            - Include questions that probe potential weaknesses to validate them
            - Mix of theoretical, practical, and scenario-based questions
            - Vary difficulty levels (easy, medium, hard)
            
            Format as JSON:
            {{
                "questions": [
                    {{
                        "question": "question text",
                        "category": "skill/domain category",
                        "difficulty": "easy|medium|hard",
                        "focus": "strength|weakness|general",
                        "domain": "domain name"
                    }}
                ]
            }}""",
            agent=domain_interviewer,
            expected_output="JSON array of domain-specific interview questions"
        )
        
        crew = Crew(
            agents=[domain_interviewer],
            tasks=[questions_task],
            verbose=True
        )
        
        # Execute asynchronously — required when called from within an async event loop
        result = await crew.kickoff_async()
        
        try:
            return parse_crew_result(result, fallback={"questions": []})
        except Exception:
            return {"questions": []}
    
    async def evaluate_interview(
        self, 
        profile_context: Dict, 
        questions: List[Dict], 
        responses: List[Dict]
    ) -> Dict:
        """Evaluate interview responses and identify strong/weak areas"""
        
        # Build interview transcript
        transcript = "INTERVIEW TRANSCRIPT\n\n"
        for i, (q, r) in enumerate(zip(questions, responses), 1):
            transcript += f"Q{i}: {q.get('question', '')}\n"
            transcript += f"A{i}: {r.get('answer', '')}\n"
            transcript += f"Confidence: {r.get('confidence', 5)}/10\n"
            transcript += f"Category: {q.get('category', 'N/A')}\n\n"
        
        # Build context
        context_str = f"""
        CANDIDATE PROFILE CONTEXT:
        - Primary Domain: {profile_context.get('primary_domain', 'Unknown')}
        - All Skills: {', '.join(profile_context.get('all_skills', []))}
        - Technical Strengths: {', '.join(profile_context.get('technical_strengths', []))}
        - Potential Weaknesses: {', '.join(profile_context.get('potential_weaknesses', []))}
        
        {profile_context.get('profile_context', '')}
        
        {transcript}
        """
        
        # Create agents
        response_evaluator = self.get_response_evaluator()
        strength_weakness_analyzer = self.get_strength_weakness_analyzer()
        skill_assessor = self.get_skill_assessor()
        
        # Task 1: Evaluate responses
        evaluation_task = Task(
            description=f"""Evaluate the interview responses and provide initial assessment:
            
            {context_str}
            
            Provide:
            1. Overall performance assessment
            2. Response quality for each question
            3. Areas where the candidate excelled
            4. Areas where the candidate struggled
            5. Confidence level in assessment
            
            Format as JSON:
            {{
                "overall_performance": "excellent|good|fair|poor",
                "response_evaluations": [
                    {{
                        "question_number": 1,
                        "quality": "excellent|good|fair|poor",
                        "notes": "specific notes"
                    }}
                ],
                "excels_in": ["area1", "area2"],
                "struggles_in": ["area1", "area2"],
                "assessment_confidence": number (0-100)
            }}""",
            agent=response_evaluator,
            expected_output="JSON with response evaluations"
        )
        
        # Task 2: Analyze strengths and weaknesses
        sw_analysis_task = Task(
            description=f"""Analyze the interview to identify specific strong and weak areas:
            
            {context_str}
            
            Identify:
            1. Strong areas with specific evidence from responses
            2. Weak areas with specific evidence from responses
            3. Areas that are borderline (need more probing)
            4. Domain-specific strengths
            5. Domain-specific weaknesses
            
            Format as JSON:
            {{
                "strong_areas": [
                    {{
                        "area": "specific skill/domain",
                        "evidence": ["evidence1", "evidence2"],
                        "proficiency_level": "expert|advanced|intermediate"
                    }}
                ],
                "weak_areas": [
                    {{
                        "area": "specific skill/domain",
                        "evidence": ["evidence1", "evidence2"],
                        "improvement_needed": "specific improvement suggestion"
                    }}
                ],
                "borderline_areas": ["area1", "area2"],
                "domain_strengths": ["strength1", "strength2"],
                "domain_weaknesses": ["weakness1", "weakness2"]
            }}""",
            agent=strength_weakness_analyzer,
            expected_output="JSON with strength and weakness analysis",
            context=[evaluation_task]
        )
        
        # Task 3: Provide skill assessments with percentages
        skill_assessment_task = Task(
            description=f"""Provide percentage-based skill assessments based on interview performance:
            
            {context_str}
            
            For each key skill in the candidate's profile and domain:
            1. Assign a percentage score (0-100%)
            2. Determine proficiency level
            3. Provide specific evidence from responses
            4. Compare against industry standards for the domain
            
            Format as JSON:
            {{
                "skill_assessments": [
                    {{
                        "skill_name": "skill",
                        "percentage": number (0-100),
                        "proficiency_level": "expert|advanced|intermediate|beginner|novice",
                        "evidence": ["evidence1", "evidence2"],
                        "domain_relevance": "high|medium|low"
                    }}
                ],
                "overall_domain_score": number (0-100),
                "domain_readiness": "ready|almost_ready|needs_improvement|not_ready"
            }}""",
            agent=skill_assessor,
            expected_output="JSON with percentage-based skill assessments",
            context=[evaluation_task, sw_analysis_task]
        )
        
        crew = Crew(
            agents=[response_evaluator, strength_weakness_analyzer, skill_assessor],
            tasks=[evaluation_task, sw_analysis_task, skill_assessment_task],
            verbose=True
        )
        
        # Execute asynchronously — required when called from within an async event loop
        result = await crew.kickoff_async()
        
        # Parse result — handles CrewOutput objects and markdown code fences
        fallback = {
            "error": "Failed to parse interview evaluation result",
            "raw_result": str(result)
        }
        return parse_crew_result(result, fallback=fallback)
