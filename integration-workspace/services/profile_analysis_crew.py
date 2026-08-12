from crewai import Agent, Task, Crew, LLM
from config import settings
from typing import Dict, List, Any
import json
from utils import parse_crew_result, get_default_llm


class ProfileAnalysisCrew:
    """Separate crew dedicated to analyzing profiles (resume, GitHub) and extracting context"""
    
    def __init__(self):
        self.llm = get_default_llm(temperature=0.3)
    
    def get_resume_extractor(self) -> Agent:
        """Agent to extract information from resume text"""
        return Agent(
            role="Resume Extractor",
            goal="Extract comprehensive technical information, skills, experience, and achievements from resume text",
            backstory="""You are an expert resume analyzer with deep knowledge of technical roles and 
            technologies. You can identify skills, frameworks, tools, experience levels, and achievements 
            from resume content. You understand industry terminology and can infer proficiency levels.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def get_github_analyzer(self) -> Agent:
        """Agent to analyze GitHub profile and repositories"""
        return Agent(
            role="GitHub Profile Analyst",
            goal="Analyze GitHub profiles to extract technical skills, project experience, and code quality indicators",
            backstory="""You are an expert code analyst who can evaluate GitHub profiles to understand a 
            developer's technical capabilities. You analyze repository languages, commit patterns, project 
            complexity, and community engagement to assess technical proficiency.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def get_domain_classifier(self) -> Agent:
        """Agent to classify the candidate's technical domain"""
        return Agent(
            role="Technical Domain Classifier",
            goal="Classify the candidate's primary technical domain and identify secondary domains based on their profile",
            backstory="""You are an expert technical recruiter who understands various engineering domains 
            (Backend, Frontend, Full Stack, DevOps, Data Science, Mobile, etc.). You can accurately classify 
            a candidate's primary domain based on their skills, experience, and project history.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def get_profile_synthesizer(self) -> Agent:
        """Agent to synthesize all profile information into a comprehensive context"""
        return Agent(
            role="Profile Synthesizer",
            goal="Synthesize resume, GitHub, and domain analysis into a comprehensive candidate profile context",
            backstory="""You are an expert technical profiler who can combine multiple sources of information 
            into a coherent and comprehensive candidate profile. You identify key themes, skill clusters, 
            and provide context for interview preparation.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    async def analyze_profile(
        self, 
        resume_text: str = None, 
        github_data: Dict = None,
        provided_skills: List[str] = None,
        experience_years: float = 0,
        target_role: str = None,
        linkedin_url: str = None,
        portfolio_url: str = None,
        web_profile_data: Dict = None
    ) -> Dict:
        """Run the profile analysis crew to extract comprehensive context"""
        
        # Build profile input
        profile_input = f"""
        CANDIDATE INFORMATION:
        - Target Role: {target_role or 'Not specified'}
        - Experience Years: {experience_years}
        - Provided Skills: {', '.join(provided_skills or [])}
        - LinkedIn URL: {linkedin_url or 'N/A'}
        - Portfolio URL: {portfolio_url or 'N/A'}
        """
        
        if resume_text:
            profile_input += f"\n\nRESUME CONTENT:\n{resume_text}"
        
        if github_data:
            profile_input += f"\n\nGITHUB PROFILE DATA:\n{json.dumps(github_data, indent=2)}"

        if web_profile_data:
            profile_input += f"\n\nWEB/PORTFOLIO ANALYSIS DATA:\n{json.dumps(web_profile_data, indent=2)}"

        
        # Create agents
        resume_extractor = self.get_resume_extractor()
        github_analyzer = self.get_github_analyzer()
        domain_classifier = self.get_domain_classifier()
        profile_synthesizer = self.get_profile_synthesizer()
        
        # Task 1: Extract resume information
        resume_task = Task(
            description=f"""Extract comprehensive information from the resume:
            
            {profile_input}
            
            Extract and provide:
            1. All technical skills (languages, frameworks, tools, databases)
            2. Work experience with roles and durations
            3. Projects and their technologies
            4. Achievements and impact
            5. Education and certifications
            6. Inferred proficiency levels for key skills
            
            Format as JSON:
            {{
                "extracted_skills": ["skill1", "skill2"],
                "experience_details": [
                    {{
                        "role": "role",
                        "company": "company",
                        "duration": "duration",
                        "technologies": ["tech1", "tech2"]
                    }}
                ],
                "projects": [
                    {{
                        "name": "project",
                        "technologies": ["tech1", "tech2"],
                        "description": "description"
                    }}
                ],
                "achievements": ["achievement1", "achievement2"],
                "education": ["education1"],
                "skill_proficiency": {{
                    "skill": "beginner|intermediate|advanced|expert"
                }}
            }}""",
            agent=resume_extractor,
            expected_output="JSON with extracted resume information"
        )
        
        # Task 2: Analyze GitHub profile
        github_task = Task(
            description=f"""Analyze the GitHub profile data:
            
            {json.dumps(github_data, indent=2) if github_data else "No GitHub data provided"}
            
            Provide:
            1. Primary programming languages and their usage patterns
            2. Code quality indicators (stars, forks, contributions)
            3. Project diversity and complexity
            4. Collaboration indicators
            5. Technology stack preferences
            
            Format as JSON:
            {{
                "primary_languages": ["lang1", "lang2"],
                "code_quality_indicators": {{
                    "total_stars": number,
                    "total_forks": number,
                    "activity_level": "low|medium|high"
                }},
                "project_diversity": "low|medium|high",
                "collaboration_score": "low|medium|high",
                "technology_stack": ["tech1", "tech2"],
                "github_skills": ["skill1", "skill2"]
            }}""",
            agent=github_analyzer,
            expected_output="JSON with GitHub analysis"
        )
        
        # Task 3: Classify technical domain
        domain_task = Task(
            description=f"""Based on all available information, classify the candidate's technical domain:
            
            {profile_input}
            
            Identify:
            1. Primary domain (e.g., Backend Engineer, Frontend Engineer, Full Stack, DevOps, Data Scientist)
            2. Secondary domains (if applicable)
            3. Domain-specific strengths
            4. Recommended focus areas for interview
            
            Format as JSON:
            {{
                "primary_domain": "domain name",
                "secondary_domains": ["domain1", "domain2"],
                "domain_confidence": number (0-100),
                "domain_specific_strengths": ["strength1", "strength2"],
                "interview_focus_areas": ["area1", "area2"],
                "domain_rationale": "explanation of domain classification"
            }}""",
            agent=domain_classifier,
            expected_output="JSON with domain classification",
            context=[resume_task, github_task]
        )
        
        # Task 4: Synthesize profile
        synthesis_task = Task(
            description=f"""Synthesize all analysis into a comprehensive profile context:
            
            Combine the resume extraction, GitHub analysis, and domain classification into a unified 
            candidate profile that will be used for interview preparation.
            
            Format as JSON:
            {{
                "candidate_summary": "brief summary",
                "primary_domain": "domain",
                "all_skills": ["skill1", "skill2"],
                "skill_clusters": {{
                    "cluster_name": ["skill1", "skill2"]
                }},
                "experience_highlights": ["highlight1", "highlight2"],
                "technical_strengths": ["strength1", "strength2"],
                "potential_weaknesses": ["weakness1", "weakness2"],
                "interview_readiness": "low|medium|high",
                "recommended_interview_depth": "basic|intermediate|advanced",
                "profile_context": "detailed context for interview preparation"
            }}""",
            agent=profile_synthesizer,
            expected_output="JSON with comprehensive synthesized profile",
            context=[resume_task, github_task, domain_task]
        )
        
        # Create crew
        crew = Crew(
            agents=[resume_extractor, github_analyzer, domain_classifier, profile_synthesizer],
            tasks=[resume_task, github_task, domain_task, synthesis_task],
            verbose=True
        )
        
        # Execute asynchronously — required when called from within an async event loop
        result = await crew.kickoff_async()
        
        # Parse result — handles CrewOutput objects and markdown code fences
        fallback = {
            "error": "Failed to parse profile analysis result",
            "raw_result": str(result)
        }
        return parse_crew_result(result, fallback=fallback)
