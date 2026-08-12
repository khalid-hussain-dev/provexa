from abc import ABC, abstractmethod
from typing import Any, Protocol


class IntelligenceServiceInterface(ABC):
    """Boundary for future Intelligence Builder operations.

    Methods intentionally define contracts only. No AI, CrewAI, LLM,
    persistence, or fake production behavior is implemented in this batch.
    """

    @abstractmethod
    async def analyze_candidate(self, candidate_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def analyze_job(self, job_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def match_candidate_to_job(self, candidate_payload: dict[str, Any], job_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def create_interview(self, candidate_payload: dict[str, Any], job_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def evaluate_interview(self, interview_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def generate_course(self, candidate_payload: dict[str, Any], goals_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def generate_resume(self, candidate_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class IntelligenceServiceProvider(Protocol):
    def get_intelligence_service(self) -> IntelligenceServiceInterface:
        ...
