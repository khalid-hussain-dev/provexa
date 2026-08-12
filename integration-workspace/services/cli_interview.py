import asyncio
import io
import sys

# Force UTF-8 stdout on Windows so emojis display correctly
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from typing import List
from models import CandidateProfile, InterviewQuestion, InterviewResponse
from interview_system import InterviewSystem
from job_service import JobRecommendationService

# ── Helpers ───────────────────────────────────────────────────────────────────

SEP = "-" * 62

def banner(text: str):
    print(f"\n{'=' * 62}")
    print(f"  {text}")
    print(f"{'=' * 62}\n")

def section(text: str):
    print(f"\n{SEP}")
    print(f"  {text}")
    print(SEP)

def _level_from_years(years: float) -> str:
    """
    Translates raw experience years into an interview DIFFICULTY level.
    This is ONLY used to set question depth — job matching uses the
    AI-assessed level from the evaluation result, not this value.
    """
    if years < 1:
        return "fresher"
    elif years < 3:
        return "junior"
    elif years < 6:
        return "mid"
    else:
        return "senior"

# ── Main interview flow ───────────────────────────────────────────────────────

async def run_interactive_interview():
    banner("AI INTERVIEW & ASSESSMENT SYSTEM — INTERACTIVE CLI")

    # ── Step 0: Gather candidate info ────────────────────────────────────────
    print("Please fill in your profile details.\n")
    name         = input("Full name                 : ").strip() or "Candidate"
    email        = input("Email                     : ").strip() or "candidate@example.com"
    target_role  = input("Target role               : ").strip() or "Software Developer"
    exp_str      = input("Years of experience       : ").strip() or "0"
    try:
        experience_years = float(exp_str)
    except ValueError:
        experience_years = 0.0

    skills_raw = input("Core skills (comma-sep)   : ").strip()
    skills     = [s.strip() for s in skills_raw.split(",") if s.strip()] or ["Python"]

    github_url      = input("GitHub URL (optional)     : ").strip() or None
    linkedin_url    = input("LinkedIn URL (optional)   : ").strip() or None
    portfolio_url   = input("Portfolio URL (optional)  : ").strip() or None
    additional_info = input("Additional info (optional): ").strip() or None

    candidate = CandidateProfile(
        name=name, email=email, target_role=target_role,
        experience_years=experience_years, github_url=github_url,
        linkedin_url=linkedin_url, portfolio_url=portfolio_url,
        additional_info=additional_info, skills=skills,
    )

    interview_level = _level_from_years(experience_years)

    system      = InterviewSystem()
    job_service = JobRecommendationService()

    # ── Step 1: Profile analysis ─────────────────────────────────────────────
    section("Step 1 / 4 — Analysing Your Profile (AI is thinking...)")
    try:
        profile_context = await system.prepare_candidate_profile(candidate)
        print(f"  Domain    : {profile_context.get('primary_domain', target_role)}")
        print(f"  Level     : {interview_level.capitalize()} (based on {experience_years} yrs — questions calibrated accordingly)")
        print(f"  Summary   : {profile_context.get('candidate_summary', 'N/A')}")
    except Exception as e:
        print(f"  [!] Profile analysis issue: {e}")
        print("  Continuing with provided skills...")
        profile_context = {
            "name": name,
            "primary_domain": target_role,
            "all_skills": skills,
            "experience_years": experience_years,
            "target_role": target_role,
            "recommended_interview_depth": interview_level,
            "candidate_summary": f"{name}, targeting {target_role} with {experience_years} year(s) of experience.",
        }

    # Inject the difficulty level so the question-generation crew can calibrate
    profile_context["interview_difficulty"] = interview_level

    # ── Step 2: Generate questions ───────────────────────────────────────────
    section("Step 2 / 4 — Generating Interview Questions...")
    num_q_str = input("  How many questions? [Default: 3]: ").strip()
    num_questions = int(num_q_str) if num_q_str.isdigit() and int(num_q_str) > 0 else 3

    try:
        raw_questions = await system.generate_interview_questions(
            profile_context, num_questions=num_questions
        )
    except Exception as e:
        print(f"\n  [!] Question generation error: {e}")
        return

    if not raw_questions:
        print("\n  [!] No questions were generated. Exiting.")
        return

    print(f"\n  {len(raw_questions)} question(s) ready. Interview starting now!\n")

    # ── Step 3: One-by-one interactive Q&A ───────────────────────────────────
    responses: List[InterviewResponse] = []
    questions_list: List[InterviewQuestion] = []

    for idx, q in enumerate(raw_questions, 1):
        q_obj = InterviewQuestion(
            question=q.question if hasattr(q, "question") else q.get("question", f"Question {idx}"),
            category=q.category if hasattr(q, "category") else q.get("category", "General"),
            difficulty=q.difficulty if hasattr(q, "difficulty") else q.get("difficulty", "medium"),
        )
        questions_list.append(q_obj)

        print(f"\n{SEP}")
        print(f"  Question {idx} of {len(raw_questions)}")
        print(f"  Category  : {q_obj.category}  |  Difficulty: {q_obj.difficulty.upper()}")
        print(f"{SEP}")
        print(f"\n  {q_obj.question}\n")

        answer = ""
        while not answer:
            answer = input("  Your answer: ").strip()
            if not answer:
                print("  [!] Answer cannot be empty.")

        conf_str = input("  Confidence (1–10) [Default: 7]: ").strip()
        confidence = int(conf_str) if conf_str.isdigit() and 1 <= int(conf_str) <= 10 else 7

        responses.append(InterviewResponse(
            question_id=str(idx - 1),
            answer=answer,
            confidence=confidence,
        ))

    # ── Step 4: Evaluate ─────────────────────────────────────────────────────
    section("Step 3 / 4 — Evaluating Your Responses (AI is scoring...)")
    try:
        result = await system.evaluate_interview_responses(
            profile_context, questions_list, responses
        )
    except Exception as e:
        print(f"\n  [!] Evaluation error: {e}")
        return

    # ── Print final assessment ────────────────────────────────────────────────
    banner("YOUR INTERVIEW RESULTS")

    print(f"  Candidate       : {result.candidate_name}")
    print(f"  Target Role     : {result.target_role}")
    print(f"  Overall Score   : {result.overall_score:.1f} / 100")
    print(f"  Assessed Level  : {result.assessed_level.capitalize()}")
    print(f"  Role Match      : {result.role_match_percentage:.1f}%")

    if result.role_match_percentage >= 75:
        match_msg = "Great match — you are well-aligned with your target role!"
    elif result.role_match_percentage >= 50:
        match_msg = "Decent match — a few gaps to fill before you are fully ready."
    elif result.role_match_percentage >= 30:
        match_msg = "Partial match — significant skill building recommended."
    else:
        match_msg = "Low match — consider internships or a learning phase first."
    print(f"\n  Assessment      : {match_msg}")

    if result.skill_assessments:
        print(f"\n{SEP}")
        print("  SKILL BREAKDOWN")
        print(SEP)
        for s in result.skill_assessments:
            bar_len = int(s.percentage / 5)
            bar = "#" * bar_len + "." * (20 - bar_len)
            print(f"  {s.skill_name:<22} [{bar}] {s.percentage:.0f}%  ({s.strength_level})")

    if result.analysis.strengths:
        print(f"\n{SEP}")
        print("  STRENGTHS")
        print(SEP)
        for st in result.analysis.strengths:
            print(f"  + {st}")

    if result.analysis.weaknesses:
        print(f"\n{SEP}")
        print("  AREAS TO IMPROVE")
        print(SEP)
        for wk in result.analysis.weaknesses:
            print(f"  - {wk}")

    if result.analysis.improvement_areas:
        print(f"\n{SEP}")
        print("  BORDERLINE SKILLS (need more practice)")
        print(SEP)
        for ar in result.analysis.improvement_areas:
            print(f"  ~ {ar}")

    # ── Step 4.5: Generate Targeted Crash Course (Strategic Director + Course Creator) ──
    section("TARGETED CRASH COURSE GENERATION (AI Learning Director is working...)")
    try:
        detailed_course = await system.generate_targeted_course(
            target_role=result.target_role,
            current_score=result.overall_score,
            weaknesses=result.analysis.weaknesses,
            improvement_areas=result.analysis.improvement_areas
        )
        result.detailed_course = detailed_course

        print(f"\n  Course Title : {detailed_course.title}")
        print(f"  Score Target : {detailed_course.current_score:.0f}% → {detailed_course.target_score:.0f}%")
        print(f"  Selected Priority Skills (Selected 2-3 essential topics):")
        for s in detailed_course.selected_priority_skills:
            print(f"    • {s}")
        print(f"\n  Summary: {detailed_course.summary}\n")

        for idx, mod in enumerate(detailed_course.modules, 1):
            print(f"{SEP}")
            print(f"  MODULE {idx}: {mod.module_title.upper()} ({mod.skill_name})")
            print(SEP)
            print(f"\n  [CONCEPT OVERVIEW]\n  {mod.concept_explanation}\n")
            print(f"  [PRACTICAL CODE EXAMPLE]\n{mod.code_example}\n")
            print(f"  [VALIDATION EXERCISE / CODE QUESTION]\n  {mod.validation_exercise}\n")
            if mod.solution_hint:
                print(f"  [HINT / SOLUTION APPROACH]\n  {mod.solution_hint}\n")

        # Interactive Course Completion & CV Injection
        comp_choice = input("\n  Mark course as 'COMPLETED' and inject new skills into your CV? (y/n) [Default: y]: ").strip().lower()
        if comp_choice in ("", "y", "yes"):
            resume_input = candidate.resume_text or f"NAME: {candidate.name}\nROLE: {candidate.target_role}\nSKILLS: {', '.join(candidate.skills)}"
            opt_res = await system.optimize_resume(
                resume_text=resume_input,
                newly_learned_skills=detailed_course.selected_priority_skills
            )
            print(f"\n{SEP}")
            print("  ATS RESUME OPTIMIZATION RESULT (New Skills Injected)")
            print(SEP)
            print(f"  Changes Summary: {opt_res.summary_of_changes}\n")
            print(f"  UPDATED RESUME TEXT:\n{opt_res.updated_resume_text}\n")
    except Exception as e:
        print(f"  [!] Course generation error: {e}")

    print(f"\n{SEP}")
    print("  INTERVIEW SUMMARY")
    print(SEP)
    print(f"\n{result.interview_summary}\n")

    # ── Step 5: Job / Internship recommendations ──────────────────────────────
    section("Step 4 / 4 — Job Recommendations")

    search = input("  Fetch real job listings now? (y/n) [Default: y]: ").strip().lower()
    if search in ("", "y", "yes"):
        location = input("  Preferred location (leave blank for Remote): ").strip() or None
        num_jobs_str = input("  How many listings to show? [Default: 5]: ").strip()
        num_jobs = int(num_jobs_str) if num_jobs_str.isdigit() and int(num_jobs_str) > 0 else 5

        print("\n  Searching listings...\n")
        try:
            jobs = await job_service.recommend_jobs(result, location=location, limit=num_jobs)
        except Exception as e:
            print(f"  [!] Job fetch error: {e}")
            jobs = []

        if jobs:
            listing_label = "INTERNSHIP" if jobs[0].listing_type == "internship" else "JOB"
            print(f"\n{SEP}")
            print(f"  MATCHED {listing_label} LISTINGS  (assessed level: {result.assessed_level})")
            print(SEP)
            for i, j in enumerate(jobs, 1):
                print(f"\n  {i}. {j.job_title}")
                print(f"     Company  : {j.company}")
                print(f"     Location : {j.location or 'Remote'}")
                print(f"     Salary   : {j.salary_range or 'Not disclosed'}")
                print(f"     Match    : {j.match_percentage:.0f}%")
                if j.url:
                    print(f"     Apply    : {j.url}")
        else:
            print("  No listings found. Try adjusting your location or check API credentials.")
    else:
        print("  Skipped job search.")

    banner("Interview Complete — Good luck!")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_interactive_interview())
