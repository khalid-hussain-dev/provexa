from fastapi import status

from app.core.errors import AppError


class DependencyUnavailableError(AppError):
    """A required Phase 1 infrastructure dependency is unavailable."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            "DEPENDENCY_UNAVAILABLE",
            message,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            details,
        )


class InvalidIntelligenceOutputError(AppError):
    """Validated boundary rejected an Intelligence result."""

    def __init__(self, message: str = "Intelligence output failed validation", details: dict | None = None) -> None:
        super().__init__(
            "INVALID_INTELLIGENCE_OUTPUT",
            message,
            status.HTTP_502_BAD_GATEWAY,
            details,
        )


class IncompleteInterviewError(AppError):
    """The transcript is not complete enough for Intelligence evaluation."""

    def __init__(self, message: str = "Answer every interview question before completing") -> None:
        super().__init__("INCOMPLETE_INTERVIEW", message, status.HTTP_409_CONFLICT)
