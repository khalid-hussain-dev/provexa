from __future__ import annotations

from typing import Any, Callable


def create_provexa_auth_router(
    *,
    db_session_provider: Callable[[Any], Any],
    settings_provider: Callable[[Any], Any] | None = None,
    session_store_provider: Callable[[Any], Any],
    prefix: str = "/api/v1/authkit",
) -> Any:
    """Build an opt-in router without replacing PROVEXA's existing auth routes."""

    from ...fastapi.router import create_auth_router
    from .repository import ProvexaUserRepository
    from .settings import build_provexa_config

    def repository_provider(request: Any) -> ProvexaUserRepository:
        return ProvexaUserRepository.from_session(db_session_provider(request))

    def config_provider(request: Any) -> Any:
        settings = settings_provider(request) if settings_provider else None
        return build_provexa_config(settings)

    def service_provider(request: Any) -> Any:
        from ...service import AuthService

        return AuthService(repository_provider(request), config_provider(request))

    return create_auth_router(
        repository_provider=repository_provider,
        config_provider=config_provider,
        session_store_provider=session_store_provider,
        service_provider=service_provider,
        prefix=prefix,
    )
