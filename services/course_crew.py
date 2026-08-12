from crewai import Agent, Task, Crew
from typing import Dict, List, Any
import json
from utils import parse_crew_result, get_default_llm
from models import DetailedCourse, CourseModule, ResumeOptimizationResult


class CourseGeneratorCrew:
    """
    Crew dedicated to:
    1. Strategic skill selection (selecting 2-3 essential skills to bridge score gap).
    2. Detailed crash course generation (modules with concept overview, code examples, validation exercises).
    3. ATS Resume optimization (injecting newly learned course skills into existing resume text).
    """

    def __init__(self):
        self.llm = get_default_llm(temperature=0.4)

    def get_strategic_learning_director(self) -> Agent:
        """Agent to select top 2-3 priority skills for targeted upskilling loop"""
        return Agent(
            role="Strategic Learning Director",
            goal="Filter candidate weakness list to select exactly 2 to 3 priority skills essential for the target role and realistic score progression",
            backstory="""You are a Strategic Learning Director managing upskilling loops. 
            You evaluate overall candidate readiness and select only 2 to 3 high-impact essential 
            skill gaps that will drive an incremental score improvement for the specified target role. 
            You NEVER pass huge lists of weaknesses; you focus strictly on top priorities.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )

    def get_technical_course_creator(self) -> Agent:
        """Agent to build detailed bite-sized crash course with code examples & validation exercises"""
        return Agent(
            role="Technical Course Creator",
            goal="Generate a detailed, bite-sized crash course with practical code snippets and validation exercises for priority topics",
            backstory="""You are a senior technical curriculum author. You design hands-on crash courses 
            for developers. For each selected topic, you write clear concept summaries, complete working 
            code examples, and practical validation exercises/code questions with solution hints.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )

    def get_ats_resume_optimizer(self) -> Agent:
        """Agent to seamlessly inject newly mastered skills into resume text"""
        return Agent(
            role="ATS Resume Optimizer",
            goal="Inject newly mastered course skills into the appropriate sections of an existing resume without altering formatting",
            backstory="""You are an expert ATS Resume Optimizer. You take a user's existing resume text and 
            a set of newly mastered skills, then seamlessly inject those skills into the 'Skills', 'Technologies', 
            or experience sections. You preserve original formatting and do NOT rewrite the entire resume.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )

    async def generate_targeted_course(
        self,
        target_role: str,
        current_score: float,
        all_weaknesses: List[str],
        improvement_areas: List[str] = None
    ) -> DetailedCourse:
        """
        Run Strategic Learning Director + Technical Course Creator to build a targeted crash course.
        """
        target_score = min(100.0, round(current_score + 15.0, 1))
        all_gaps = (all_weaknesses or []) + (improvement_areas or [])
        if not all_gaps:
            all_gaps = [f"Advanced {target_role} Architecture", "System Design & Optimization"]

        director = self.get_strategic_learning_director()
        course_creator = self.get_technical_course_creator()

        # Task 1: Select 2-3 essential topics
        selection_task = Task(
            description=f"""You are a Strategic Learning Director managing a candidate's upskilling loop.
            
            CANDIDATE STATE:
            - Target Role: {target_role}
            - Current Readiness Score: {current_score:.1f}%
            - Sprint Target Score: {target_score:.1f}%
            - Identified Weaknesses & Gaps: {json.dumps(all_gaps)}
            
            YOUR TASK:
            1. Review the list of weaknesses.
            2. Select EXACTLY 2 to 3 essential skills that are absolutely critical for their target job level ({target_role}).
            3. Do NOT pass the entire list. Filter out non-essentials.
            
            Format as JSON:
            {{
                "selected_priority_skills": ["skill 1", "skill 2"],
                "selection_rationale": "Explanation of why these 2-3 topics were prioritized."
            }}""",
            agent=director,
            expected_output="JSON containing selected_priority_skills and rationale"
        )

        # Task 2: Build detailed course modules
        course_task = Task(
            description=f"""You are a Technical Course Creator. Generate a detailed bite-sized crash course strictly covering the 2-3 selected priority topics from the Strategic Learning Director.
            
            REQUIREMENTS:
            - Create 1 module for each selected priority topic.
            - Each module MUST include:
              1. "module_title": Clear descriptive title.
              2. "skill_name": Target skill name.
              3. "concept_explanation": In-depth theoretical overview & key concepts (2-3 paragraphs).
              4. "code_example": Practical, executable code snippet/example demonstrating best practices.
              5. "validation_exercise": A concrete code question / challenge for candidate to solve.
              6. "solution_hint": Solution approach or code hint for validation exercise.
            
            Format as JSON:
            {{
                "course_title": "Targeted Upskilling: {target_role}",
                "summary": "Brief overview of this sprint course",
                "modules": [
                    {{
                        "module_title": "Module Title",
                        "skill_name": "Skill",
                        "concept_explanation": "Detailed concept text...",
                        "code_example": "def example(): ...",
                        "validation_exercise": "Question / exercise text...",
                        "solution_hint": "Hint text..."
                    }}
                ]
            }}""",
            agent=course_creator,
            expected_output="JSON with detailed course modules",
            context=[selection_task]
        )

        crew = Crew(
            agents=[director, course_creator],
            tasks=[selection_task, course_task],
            verbose=True
        )

        raw_result = await crew.kickoff_async()
        parsed = parse_crew_result(raw_result, fallback={})
        if isinstance(parsed, list):
            parsed = parsed[0] if (parsed and isinstance(parsed[0], dict)) else {}
        if not isinstance(parsed, dict):
            parsed = {}

        modules_data = parsed.get("modules", [])
        modules = [
            CourseModule(
                module_title=m.get("module_title", f"Module {i+1}"),
                skill_name=m.get("skill_name", target_role),
                concept_explanation=m.get("concept_explanation", "Concept overview."),
                code_example=m.get("code_example", "# Code example"),
                validation_exercise=m.get("validation_exercise", "Practical exercise"),
                solution_hint=m.get("solution_hint")
            )
            for i, m in enumerate(modules_data)
        ]

        priority_skills = parsed.get("selected_priority_skills", [m.skill_name for m in modules])

        return DetailedCourse(
            title=parsed.get("course_title", f"Sprint Upskilling: {target_role}"),
            target_role=target_role,
            current_score=current_score,
            target_score=target_score,
            selected_priority_skills=priority_skills,
            modules=modules,
            summary=parsed.get("summary", f"Targeted course to raise score from {current_score:.0f}% to {target_score:.0f}%.")
        )

    async def optimize_resume(
        self,
        resume_text: str,
        newly_learned_skills: List[str]
    ) -> ResumeOptimizationResult:
        """
        Run ATS Resume Optimizer to inject newly learned skills into existing resume text.
        """
        optimizer = self.get_ats_resume_optimizer()

        opt_task = Task(
            description=f"""You are an ATS Resume Optimizer.
            
            The candidate has just completed a targeted course and mastered the following skills:
            {json.dumps(newly_learned_skills)}
            
            ORIGINAL RESUME TEXT:
            {resume_text}
            
            YOUR TASK:
            1. Review the existing resume text.
            2. Seamlessly inject these newly mastered skills into the appropriate 'Skills', 'Technologies', or experience bullet points.
            3. Do NOT rewrite the entire resume or change its fundamental formatting.
            4. Output the updated resume text directly.
            
            Format as JSON:
            {{
                "updated_resume_text": "Complete updated resume text...",
                "injected_skills": {json.dumps(newly_learned_skills)},
                "summary_of_changes": "Brief summary of sections updated with new skills."
            }}""",
            agent=optimizer,
            expected_output="JSON with updated_resume_text and summary_of_changes"
        )

        crew = Crew(
            agents=[optimizer],
            tasks=[opt_task],
            verbose=True
        )

        raw_result = await crew.kickoff_async()
        parsed = parse_crew_result(raw_result, fallback={})
        if isinstance(parsed, list):
            parsed = parsed[0] if (parsed and isinstance(parsed[0], dict)) else {}
        if not isinstance(parsed, dict):
            parsed = {}

        updated_text = parsed.get("updated_resume_text") or (
            resume_text + f"\n\nAdditional Skills (Mastered): {', '.join(newly_learned_skills)}"
        )

        return ResumeOptimizationResult(
            original_resume_text=resume_text,
            updated_resume_text=updated_text,
            injected_skills=parsed.get("injected_skills", newly_learned_skills),
            summary_of_changes=parsed.get("summary_of_changes", "Successfully injected course skills into resume.")
        )
