from __future__ import annotations

import os

from .errors import DependencyUnavailableError


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def validate_database_configuration() -> str:
    """Require PostgreSQL for the host, with an explicit test-only SQLite escape hatch."""

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise DependencyUnavailableError(
            "DATABASE_URL must be configured for the Intelligence host"
        )

    if "CHANGE_ME" in database_url.upper():
        raise DependencyUnavailableError(
            "DATABASE_URL still contains a placeholder credential; replace it before starting the host",
            {"database_engine": database_url.split(":", 1)[0]},
        )

    if database_url.startswith(("postgresql://", "postgresql+")) and not database_url.startswith(
        "postgresql+asyncpg://"
    ):
        return database_url

    test_mode = os.getenv("APP_ENV", "").strip().lower() in {"test", "testing"}
    if test_mode and _truthy(os.getenv("INTEGRATION_ALLOW_SQLITE_TESTS")) and database_url.startswith("sqlite"):
        return database_url

    raise DependencyUnavailableError(
        "PostgreSQL is required as the durable persistence authority",
        {"database_engine": database_url.split(":", 1)[0]},
    )


def validate_security_configuration() -> None:
    secret = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY")
    app_env = os.getenv("APP_ENV", "").strip().lower()
    if not secret and app_env not in {"test", "testing"}:
        raise DependencyUnavailableError("JWT_SECRET or JWT_SECRET_KEY must be configured")
    if app_env not in {"development", "test", "testing"} and secret == "dev-only-change-me":
        raise DependencyUnavailableError("The development JWT secret cannot be used outside local development")


def allow_in_memory_sessions() -> bool:
    """Allow the non-durable session store only when explicitly marked local/test."""

    app_env = os.getenv("APP_ENV", "").strip().lower()
    return app_env in {"development", "test", "testing"} and _truthy(
        os.getenv("INTEGRATION_ALLOW_INMEMORY_SESSIONS")
    )
