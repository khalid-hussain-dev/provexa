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

