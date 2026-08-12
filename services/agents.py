from crewai import Agent, Task, Crew, LLM
from config import settings
from typing import List, Dict, Any


from utils import get_default_llm


class InterviewAgents:
    def __init__(self):
        self.llm = get_default_llm(temperature=0.7)
        
    def get_profile_analyzer(self) -> Agent:
        """Agent to analyze candidate's resume and GitHub profile"""
        return Agent(
            role="Technical Profile Analyzer",
            goal="Analyze candidate's resume, GitHub profile, and experience to extract skills, expertise level, and technical background",
            backstory="""You are an expert technical recruiter with 15 years of experience in analyzing 
            developer profiles. You can identify skills from resumes, GitHub repositories, and experience 
            descriptions. You understand different tech stacks and can assess proficiency levels.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def get_interviewer(self) -> Agent:
        """Agent to generate interview questions based on profile"""
        return Agent(
            role="Technical Interviewer",
            goal="Generate relevant, challenging interview questions based on the candidate's profile and target role",
            backstory="""You are a senior technical interviewer who has conducted hundreds of interviews 
            for various technical roles. You know how to ask questions that truly assess a candidate's 
            knowledge and problem-solving abilities. You tailor questions to the candidate's experience level.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def get_evaluator(self) -> Agent:
        """Agent to evaluate interview responses and assess skills"""
        return Agent(
            role="Technical Skills Evaluator",
            goal="Evaluate interview responses and provide detailed skill assessments with percentage scores",
            backstory="""You are an expert technical assessor who can accurately gauge a candidate's 
            proficiency based on their interview responses. You provide objective evaluations with 
            percentage scores and identify specific strengths and weaknesses.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def get_course_generator(self) -> Agent:
        """Agent to generate personalized learning recommendations"""
        return Agent(
            role="Learning Path Designer",
            goal="Create personalized course recommendations to help candidates improve their weaknesses and enhance their strengths",
            backstory="""You are an expert curriculum designer with deep knowledge of technical learning 
            paths. You can identify the best resources and create structured learning plans based on 
            skill gaps and career goals.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def get_career_advisor(self) -> Agent:
        """Agent to provide career advice and job matching insights"""
        return Agent(
            role="Career Advisor",
            goal="Analyze skill assessments and provide career path suggestions with job role recommendations",
            backstory="""You are a career coach specializing in tech careers. You understand the job market 
            and can match candidate profiles with suitable career paths and job roles.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
