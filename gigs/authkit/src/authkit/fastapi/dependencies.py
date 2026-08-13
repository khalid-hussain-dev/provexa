from __future__ import annotations

from typing import Any, Callable

from fastapi import Request

from ..config import AuthKitConfig
from ..errors import AuthenticationError
from ..models import AuthUser
from ..repositories import UserRepository
from ..sessions.base import SessionStore
from ..tokens import decode_access_token, require_token_purpose


Provider = Callable[[Request], Any]


def get_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationError("Authentication required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Invalid authorization header")
    return token


def get_current_payload(request: Request, config: AuthKitConfig) -> dict[str, Any]:
    return decode_access_token(get_bearer_token(request), config)


def get_current_user_dependency(
    repository_provider: Provider,
    config_provider: Provider,
    session_store_provider: Provider,
    *,
    require_purpose: str | None = None,
    reject_any_purpose: bool = True,
) -> Callable[[Request], AuthUser]:
    def dependency(request: Request) -> AuthUser:
        config: AuthKitConfig = config_provider(request)
        repository: UserRepository = repository_provider(request)
        store: SessionStore = session_store_provider(request)
        payload = get_current_payload(request, config)
        session_id = str(payload.get("jti", ""))
        if not session_id or store.is_revoked(session_id):
            raise AuthenticationError("Access token has been revoked")
        session = store.get(session_id)
        if not session or str(session.get("user_id")) != str(payload.get("sub")):
            raise AuthenticationError("Session is missing or expired")
        purpose = payload.get("purpose")
        if require_purpose is not None:
            require_token_purpose(payload, require_purpose)
        elif reject_any_purpose and purpose:
            raise AuthenticationError("Two-factor verification required")
        user = repository.get_by_id(str(payload["sub"]))
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        return user

    return dependency
