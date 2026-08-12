from typing import Any

from app.services.intelligence.interfaces import IntelligenceServiceInterface


class IntelligenceServiceNotConfigured(IntelligenceServiceInterface):
    """Explicit placeholder used until Intelligence Builder provides implementation."""

    async def analyze_candidate(self, candidate_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Intelligence service is not configured")

    async def analyze_job(self, job_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Intelligence service is not configured")

    async def match_candidate_to_job(self, candidate_payload: dict[str, Any], job_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Intelligence service is not configured")

    async def create_interview(self, candidate_payload: dict[str, Any], job_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Intelligence service is not configured")

    async def evaluate_interview(self, interview_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Intelligence service is not configured")

    async def generate_course(self, candidate_payload: dict[str, Any], goals_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Intelligence service is not configured")

    async def generate_resume(self, candidate_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Intelligence service is not configured")
