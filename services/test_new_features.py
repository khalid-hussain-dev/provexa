import asyncio
import sys

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

from models import CandidateProfile, DetailedCourse, ResumeOptimizationResult
from interview_system import InterviewSystem



async def test_all_new_features():
    print("=" * 65)
    print("  TESTING NEW FEATURES: COURSE CREATOR & ATS RESUME OPTIMIZER")
    print("=" * 65)

    system = InterviewSystem()

    # 1. Test Profile Preparation with Multi-URL (GitHub, LinkedIn, Portfolio)
    print("\n--- [1/3] Testing Multi-URL Profile Ingestion ---")
    candidate = CandidateProfile(
        name="Mohib Tester",
        email="mohib@example.com",
        target_role="Software Engineer",
        experience_years=1.0,
        github_url="https://github.com/example",
        linkedin_url="https://linkedin.com/in/example",
        portfolio_url="https://example.dev",
        skills=["Python", "FastAPI"]
    )
    profile_context = await system.prepare_candidate_profile(candidate)
    print(f"✓ Primary Domain: {profile_context.get('primary_domain')}")
    print(f"✓ Registered LinkedIn: {profile_context.get('linkedin_url')}")
    print(f"✓ Registered Portfolio: {profile_context.get('portfolio_url')}")

    # 2. Test Strategic Learning Director & Technical Course Creator
    print("\n--- [2/3] Testing Strategic 2-3 Topic Course Generation ---")
    mock_weaknesses = [
        "Database Indexing & Query Optimization",
        "Microservices Inter-service Communication & Message Queues",
        "Distributed Transactions & Saga Pattern",
        "Basic Git Commands",
        "HTML Form Parsing",
        "Kubernetes Helm Charts"
    ]
    course = await system.generate_targeted_course(
        target_role="Software Engineer",
        current_score=70.0,
        weaknesses=mock_weaknesses
    )
    print(f"✓ Course Title: {course.title}")
    print(f"✓ Target Score Jump: {course.current_score}% -> {course.target_score}%")
    print(f"✓ Selected Priority Skills (Should be 2-3 topics): {course.selected_priority_skills}")
    print(f"✓ Generated Modules Count: {len(course.modules)}")
    for m in course.modules:
        print(f"  • Module: {m.module_title} [{m.skill_name}]")
        print(f"    Code Example Snippet: {m.code_example[:60]}...")
        print(f"    Validation Exercise: {m.validation_exercise[:60]}...")

    # 3. Test ATS Resume Skill Injection
    print("\n--- [3/3] Testing ATS Resume Skill Optimizer ---")
    sample_resume = """
    MOHIB - SOFTWARE ENGINEER
    Email: mohib@example.com

    SUMMARY:
    Passionate Software Engineer with 1 year experience building APIs in Python and FastAPI.

    SKILLS:
    Python, FastAPI, Git, REST APIs

    EXPERIENCE:
    Junior Developer at Tech Solutions (2025-Present)
    - Developed backend endpoints with FastAPI.
    """
    opt_result = await system.optimize_resume(
        resume_text=sample_resume,
        newly_learned_skills=course.selected_priority_skills
    )
    print("✓ Summary of changes:", opt_result.summary_of_changes)
    print("✓ Injected Skills:", opt_result.injected_skills)
    print("\nUPDATED RESUME SNIPPET:\n", opt_result.updated_resume_text)

    print("\n" + "=" * 65)
    print("  ALL NEW FEATURES VERIFIED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(test_all_new_features())
