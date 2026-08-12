import httpx
from typing import List, Optional
from models import InterviewResult, JobRecommendation
from config import settings


class JobRecommendationService:
    """
    Fetches job or internship listings from Adzuna based on the
    AI-assessed candidate level and strong skills — NOT raw experience years.

    Decision logic:
      assessed_level == "fresher"               → search internships
      assessed_level == "junior"                → search junior/graduate jobs
      assessed_level in ("mid", "senior")       → search by assessed level + role
      role_match_percentage < 40               → regardless of level, prefer internships
    """

    def __init__(self):
        self.app_id  = settings.ADZUNA_APP_ID
        self.app_key = settings.JOB_API_KEY
        self.base_url = "https://api.adzuna.com/v1/api/jobs"

    # ── Public entry point ────────────────────────────────────────────────────

    async def recommend_jobs(
        self,
        interview_result: InterviewResult,
        location: Optional[str] = None,
        limit: int = 5,
        country: str = "gb",   # Adzuna country code: gb, us, au, de, etc.
    ) -> List[JobRecommendation]:
        """
        Return job/internship listings matched to the candidate's AI-assessed profile.
        Falls back to mock data if the API key is missing or the call fails.
        """
        listing_type, query = self._build_search(interview_result)

        if self.app_id and self.app_key:
            try:
                results = await self._call_adzuna(
                    query=query,
                    location=location,
                    limit=limit,
                    country=country,
                    listing_type=listing_type,
                )
                if results:
                    return results
            except Exception as e:
                print(f"[JobService] Adzuna API error: {e} — using mock data")

        return self._mock_recommendations(interview_result, location, limit, listing_type)

    # ── Search query builder ──────────────────────────────────────────────────

    def _build_search(self, result: InterviewResult):
        """
        Decide listing type (job vs internship) and build a search query string
        based on the AI assessment output, not raw experience years.
        """
        level    = getattr(result, "assessed_level", "junior").lower()
        match_pct = getattr(result, "role_match_percentage", 50.0)
        role     = result.target_role

        # Top strong skills from assessment (up to 3)
        top_skills = [
            s.skill_name for s in result.skill_assessments
            if s.strength_level in ("expert", "advanced", "intermediate")
        ][:3]

        # Decide whether to look for internships or jobs
        if level == "fresher" or match_pct < 40:
            listing_type = "internship"
        else:
            listing_type = "job"

        # Build role prefix based on level
        role_prefix = {
            "fresher":  "",
            "junior":   "Junior",
            "mid":      "",
            "senior":   "Senior",
        }.get(level, "")

        query_parts = [role_prefix, role] + top_skills
        query = " ".join(p for p in query_parts if p).strip()
        if listing_type == "internship":
            query = f"{role} internship"

        return listing_type, query

    # ── Adzuna API call ───────────────────────────────────────────────────────

    async def _call_adzuna(
        self,
        query: str,
        location: Optional[str],
        limit: int,
        country: str,
        listing_type: str,
    ) -> Optional[List[JobRecommendation]]:
        """Call the Adzuna API and return parsed JobRecommendation objects."""
        url = f"{self.base_url}/{country}/search/1"
        params = {
            "app_id":       self.app_id,
            "app_key":      self.app_key,
            "what":         query,
            "results_per_page": limit,
            "content-type": "application/json",
        }
        if location:
            params["where"] = location

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        return self._parse_adzuna_response(data, listing_type)

    def _parse_adzuna_response(
        self, data: dict, listing_type: str
    ) -> List[JobRecommendation]:
        """Parse raw Adzuna JSON into JobRecommendation objects."""
        recommendations = []
        for job in data.get("results", []):
            # Extract salary range
            sal_min = job.get("salary_min")
            sal_max = job.get("salary_max")
            if sal_min and sal_max:
                salary_range = f"£{int(sal_min):,} – £{int(sal_max):,}"
            elif sal_max:
                salary_range = f"Up to £{int(sal_max):,}"
            else:
                salary_range = None

            recommendations.append(JobRecommendation(
                job_title=job.get("title", ""),
                company=job.get("company", {}).get("display_name", "N/A"),
                description=(job.get("description", "")[:300] + "..."),
                required_skills=job.get("tags", []),
                match_percentage=0.0,   # Adzuna doesn't return this; calculated below
                salary_range=salary_range,
                location=job.get("location", {}).get("display_name", "Remote"),
                url=job.get("redirect_url", ""),
                listing_type=listing_type,
            ))
        return recommendations

    # ── Mock fallback ─────────────────────────────────────────────────────────

    def _mock_recommendations(
        self,
        result: InterviewResult,
        location: Optional[str],
        limit: int,
        listing_type: str,
    ) -> List[JobRecommendation]:
        """Return mock listings when Adzuna is unavailable."""
        level = getattr(result, "assessed_level", "junior").lower()
        role  = result.target_role

        if listing_type == "internship":
            templates = [
                {
                    "title": f"{role} Intern",
                    "company": "TechStart Ltd.",
                    "description": f"Internship opportunity for aspiring {role}s. Great learning environment.",
                    "skills": ["Git", "Problem Solving", "Communication"],
                    "salary": "£15,000 – £20,000",
                },
                {
                    "title": f"Graduate {role}",
                    "company": "Innovate Corp",
                    "description": "Join our graduate scheme and kickstart your tech career.",
                    "skills": ["Python", "Agile", "REST APIs"],
                    "salary": "£20,000 – £28,000",
                },
            ]
        elif level == "senior":
            templates = [
                {
                    "title": f"Senior {role}",
                    "company": "Enterprise Solutions",
                    "description": f"Lead {role} role requiring deep expertise.",
                    "skills": ["System Design", "Mentoring", "Architecture"],
                    "salary": "£80,000 – £120,000",
                },
                {
                    "title": f"Staff {role}",
                    "company": "Scale-Up Ltd.",
                    "description": "Shape technical direction at a growing scale-up.",
                    "skills": ["Leadership", "Cloud", "Microservices"],
                    "salary": "£90,000 – £130,000",
                },
            ]
        elif level == "mid":
            templates = [
                {
                    "title": role,
                    "company": "MidTech Solutions",
                    "description": f"Mid-level {role} working on greenfield projects.",
                    "skills": ["Docker", "CI/CD", "SQL"],
                    "salary": "£45,000 – £65,000",
                },
            ]
        else:  # junior
            templates = [
                {
                    "title": f"Junior {role}",
                    "company": "GrowthTech",
                    "description": "Excellent junior position with strong mentorship.",
                    "skills": ["Python", "REST", "Git"],
                    "salary": "£28,000 – £38,000",
                },
                {
                    "title": f"Associate {role}",
                    "company": "StartupHub",
                    "description": "Fast-paced startup looking for motivated juniors.",
                    "skills": ["Agile", "API Design", "Databases"],
                    "salary": "£30,000 – £40,000",
                },
            ]

        jobs = []
        for i, t in enumerate(templates[:limit]):
            jobs.append(JobRecommendation(
                job_title=t["title"],
                company=t["company"],
                description=t["description"],
                required_skills=t["skills"],
                match_percentage=round(max(50, result.overall_score - i * 5), 1),
                salary_range=t.get("salary"),
                location=location or "Remote / Hybrid",
                url="https://www.adzuna.com/search?q=" + role.replace(" ", "+"),
                listing_type=listing_type,
            ))
        return jobs

    # ── Utility ───────────────────────────────────────────────────────────────

    def calculate_skill_match(
        self,
        job_skills: List[str],
        candidate_skills: List[str],
    ) -> float:
        """Percentage of job-required skills present in candidate profile."""
        if not job_skills:
            return 0.0
        job_lower = [s.lower() for s in job_skills]
        cand_lower = [s.lower() for s in candidate_skills]
        matches = sum(
            1 for j in job_lower
            if any(c in j or j in c for c in cand_lower)
        )
        return round((matches / len(job_skills)) * 100, 1)
