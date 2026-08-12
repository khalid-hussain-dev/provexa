"""
Example usage of the AI Interview & Assessment System
This demonstrates how to use the system programmatically
"""

from models import CandidateProfile, InterviewQuestion, InterviewResponse
from interview_system import InterviewSystem
from job_service import JobRecommendationService
import asyncio


async def main():
    """Run a complete assessment example"""
    
    # Initialize services
    interview_system = InterviewSystem()
    job_service = JobRecommendationService()
    
    # Create a candidate profile
    candidate = CandidateProfile(
        name="John Doe",
        email="john.doe@example.com",
        target_role="Backend Engineer",
        experience_years=3.5,
        github_url="https://github.com/example-user",
        skills=["Python", "Django", "PostgreSQL", "Docker", "REST APIs"],
        additional_info="Interested in microservices architecture and cloud deployment"
    )
    
    print("=" * 60)
    print("STEP 1: Analyzing Candidate Profile")
    print("=" * 60)
    
    # Prepare candidate profile
    profile_data = interview_system.prepare_candidate_profile(candidate)
    
    print(f"\nCandidate: {profile_data['name']}")
    print(f"Target Role: {profile_data['target_role']}")
    print(f"Experience: {profile_data['experience_years']} years")
    print(f"Identified Skills: {', '.join(profile_data['skills'])}")
    
    if 'github_analysis' in profile_data:
        print(f"\nGitHub Analysis:")
        print(f"- Repositories: {profile_data['github_analysis'].get('public_repos', 0)}")
        print(f"- Languages: {', '.join(list(profile_data['github_analysis'].get('languages', {}).keys())[:5])}")
    
    print("\n" + "=" * 60)
    print("STEP 2: Generating Interview Questions")
    print("=" * 60)
    
    # Generate interview questions
    questions = interview_system.generate_interview_questions(profile_data, num_questions=5)
    
    print(f"\nGenerated {len(questions)} questions:\n")
    for i, q in enumerate(questions, 1):
        print(f"Q{i}: {q.question}")
        print(f"   Category: {q.category} | Difficulty: {q.difficulty}\n")
    
    print("=" * 60)
    print("STEP 3: Simulating Interview Responses")
    print("=" * 60)
    
    # Simulate candidate responses (in real usage, these would come from the user)
    responses = [
        InterviewResponse(
            question_id="0",
            answer="I have 3 years of experience with Python, primarily using it for backend development with Django and Flask. I'm comfortable with async programming and have used FastAPI for several projects.",
            confidence=8
        ),
        InterviewResponse(
            question_id="1",
            answer="I've designed RESTful APIs following OpenAPI specifications. I understand proper HTTP methods, status codes, and authentication patterns like JWT and OAuth2.",
            confidence=7
        ),
        InterviewResponse(
            question_id="2",
            answer="I work with PostgreSQL regularly. I'm familiar with writing complex queries, indexing strategies, and have some experience with database optimization and transactions.",
            confidence=6
        ),
        InterviewResponse(
            question_id="3",
            answer="I use Docker for containerization. I can write Dockerfiles and docker-compose files. I've deployed containers to AWS ECS but have limited experience with Kubernetes.",
            confidence=5
        ),
        InterviewResponse(
            question_id="4",
            answer="I understand microservices concepts and have worked on a project with 3 microservices. I used message queues for inter-service communication. However, I haven't dealt with distributed transactions at scale.",
            confidence=4
        )
    ]
    
    print("\nSimulated responses recorded.\n")
    
    print("=" * 60)
    print("STEP 4: Evaluating Interview Responses")
    print("=" * 60)
    
    # Evaluate interview responses
    result = interview_system.evaluate_interview_responses(profile_data, questions, responses)
    
    print(f"\nOverall Score: {result.overall_score}%")
    print(f"\nSkill Assessments:")
    for skill in result.skill_assessments:
        print(f"- {skill.skill_name}: {skill.percentage}% ({skill.strength_level})")
    
    print(f"\nStrengths:")
    for strength in result.analysis.strengths:
        print(f"- {strength}")
    
    print(f"\nWeaknesses:")
    for weakness in result.analysis.weaknesses:
        print(f"- {weakness}")
    
    print(f"\nImprovement Areas:")
    for area in result.analysis.improvement_areas:
        print(f"- {area}")
    
    print(f"\nCourse Recommendations:")
    for course in result.course_recommendations:
        print(f"- {course.title} ({course.duration_weeks} weeks) - Priority: {course.priority}")
    
    print(f"\nInterview Summary:")
    print(result.interview_summary)
    
    print("\n" + "=" * 60)
    print("STEP 5: Getting Job Recommendations")
    print("=" * 60)
    
    # Get job recommendations
    jobs = await job_service.recommend_jobs(result, location="Remote", limit=3)
    
    print(f"\nRecommended Jobs:\n")
    for job in jobs:
        print(f"Position: {job.job_title}")
        print(f"Company: {job.company}")
        print(f"Match: {job.match_percentage}%")
        print(f"Salary: {job.salary_range}")
        print(f"Location: {job.location}")
        print(f"Required Skills: {', '.join(job.required_skills)}")
        print()
    
    print("=" * 60)
    print("Assessment Complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("AI Interview & Assessment System - Example Usage\n")
    asyncio.run(main())
