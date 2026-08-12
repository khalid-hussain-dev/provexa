from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, Request

from app.auth.models import User
from app.auth.repository import UserRepository, get_user_repository
from app.auth.tokens import decode_access_token, require_token_purpose
from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError

from .session_store import SessionStore


def get_session_store(request: Request) -> SessionStore:
    store = getattr(request.app.state, "integration_session_store", None)
    if store is None:
        raise AuthenticationError("Session service is not configured")
    return store


def get_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationError("Authentication required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Invalid authorization header")
    return token


def get_bearer_payload(request: Request, settings: Settings) -> dict:
    return decode_access_token(get_bearer_token(request), settings)


def _ttl_from_payload(payload: dict) -> int:
    return max(1, int(payload["exp"]) - int(datetime.now(timezone.utc).timestamp()))


def _get_session_user(
    request: Request,
    repository: UserRepository,
    settings: Settings,
    store: SessionStore,
    *,
    require_purpose: str | None,
) -> tuple[User, dict]:
    payload = get_bearer_payload(request, settings)
    session_id = str(payload.get("jti", ""))
    if not session_id or store.is_revoked(session_id):
        raise AuthenticationError("Access token has been revoked")
    session = store.get(session_id)
    if not session or str(session.get("user_id")) != str(payload.get("sub")):
        raise AuthenticationError("Session is missing or expired")
    purpose = payload.get("purpose")
    if require_purpose is None and purpose:
        raise AuthenticationError("Two-factor verification required")
    if require_purpose is not None:
        require_token_purpose(payload, require_purpose)
    user = repository.get_by_id(str(payload["sub"]))
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user, payload


def get_current_user(
    request: Request,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
    store: SessionStore = Depends(get_session_store),
) -> User:
    user, _ = _get_session_user(request, repository, settings, store, require_purpose=None)
    return user


def get_pending_two_factor_user(
    request: Request,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
    store: SessionStore = Depends(get_session_store),
) -> User:
    user, _ = _get_session_user(request, repository, settings, store, require_purpose="2fa_pending")
    return user


def get_current_payload(request: Request, settings: Settings = Depends(get_settings)) -> dict:
    return get_bearer_payload(request, settings)


def token_ttl(payload: dict) -> int:
    return _ttl_from_payload(payload)

