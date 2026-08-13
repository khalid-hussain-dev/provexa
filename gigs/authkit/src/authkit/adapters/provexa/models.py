from __future__ import annotations

from typing import Any
from uuid import UUID

from ...models import AuthUser


def to_auth_user(user: Any) -> AuthUser:
    return AuthUser(
        id=str(user.id),
        email=str(user.email),
        password_hash=str(user.password_hash),
        name=user.name,
        is_active=bool(user.is_active),
        two_factor_enabled=bool(user.two_factor_enabled),
        two_factor_secret=user.two_factor_secret,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def to_provexa_user(user: AuthUser) -> Any:
    from app.auth.models import User

    if not user.id:
        return User.create(
            email=user.email,
            password_hash=user.password_hash,
            name=user.name,
        )
    return User(
        id=UUID(str(user.id)),
        email=user.email,
        password_hash=user.password_hash,
        name=user.name,
        is_active=user.is_active,
        two_factor_enabled=user.two_factor_enabled,
        two_factor_secret=user.two_factor_secret,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
