from fastapi import Depends, Request

from app.auth.models import User
from app.auth.repository import UserRepository, get_user_repository
from app.auth.tokens import decode_access_token
from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError


def get_current_user(
    request: Request,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> User:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationError("Authentication required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Invalid authorization header")

    payload = decode_access_token(token, settings)
    user = repository.get_by_id(str(payload["sub"]))
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user
