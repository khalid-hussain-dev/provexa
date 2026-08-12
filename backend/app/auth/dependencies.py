from fastapi import Depends, Request

from app.auth.models import User
from app.auth.repository import UserRepository, get_user_repository
from app.auth.tokens import decode_access_token, require_token_purpose
from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError


def get_current_user(
    request: Request,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> User:
    payload = get_bearer_payload(request, settings)
    if payload.get("purpose"):
        raise AuthenticationError("Two-factor verification required")
    token_id = payload.get("jti")
    if token_id and repository.is_token_revoked(str(token_id)):
        raise AuthenticationError("Access token has been revoked")
    user = repository.get_by_id(str(payload["sub"]))
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user


def get_two_factor_verification_user(
    request: Request,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> User:
    payload = get_bearer_payload(request, settings)
    if payload.get("purpose") is not None:
        require_token_purpose(payload, "2fa_pending")
    token_id = payload.get("jti")
    if token_id and repository.is_token_revoked(str(token_id)):
        raise AuthenticationError("Access token has been revoked")
    user = repository.get_by_id(str(payload["sub"]))
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user


def get_bearer_payload(request: Request, settings: Settings) -> dict:
    token = get_bearer_token(request)
    return decode_access_token(token, settings)


def get_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationError("Authentication required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Invalid authorization header")
    return token
