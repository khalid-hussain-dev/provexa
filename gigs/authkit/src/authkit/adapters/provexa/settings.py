from __future__ import annotations

from typing import Any

from ...config import AuthKitConfig


def build_provexa_config(settings: Any | None = None) -> AuthKitConfig:
    if settings is None:
        from app.core.config import get_settings

        settings = get_settings()
    try:
        from integration.runtime import allow_in_memory_sessions

        allow_memory = allow_in_memory_sessions()
    except ImportError:
        allow_memory = False
    environment = str(settings.app_env)
    return AuthKitConfig(
        jwt_secret_key=str(settings.jwt_secret_key),
        jwt_access_token_minutes=int(settings.jwt_access_token_minutes),
        pending_2fa_token_minutes=int(settings.pending_2fa_token_minutes),
        password_reset_token_minutes=int(getattr(settings, "password_reset_token_minutes", 30)),
        redis_url=getattr(settings, "redis_url", None),
        session_key_prefix=str(getattr(settings, "transient_state_prefix", "provexa")),
        allow_in_memory_sessions=allow_memory,
        environment=environment,
        two_factor_issuer="PROVEXA",
        expose_password_reset_token=environment.lower() == "development",
    )
