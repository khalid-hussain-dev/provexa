from __future__ import annotations

from datetime import datetime
from typing import Any

from ...models import AuthUser
from ...repositories import UserRepository
from .models import to_auth_user, to_provexa_user


class ProvexaUserRepository:
    """AuthKit repository facade over the existing PROVEXA repository.

    The legacy repository is injected, so importing AuthKit does not require
    SQLAlchemy or the PROVEXA backend to be installed.
    """

    def __init__(self, legacy_repository: Any) -> None:
        self._legacy = legacy_repository

    @classmethod
    def from_session(cls, session: Any) -> "ProvexaUserRepository":
        from app.auth.repository import SqlAlchemyUserRepository

        return cls(SqlAlchemyUserRepository(session))

    def get_by_email(self, email: str) -> AuthUser | None:
        user = self._legacy.get_by_email(email)
        return to_auth_user(user) if user else None

    def get_by_id(self, user_id: str) -> AuthUser | None:
        user = self._legacy.get_by_id(user_id)
        return to_auth_user(user) if user else None

    def create_user(self, *, email: str, password_hash: str, name: str | None = None) -> AuthUser:
        user = to_provexa_user(
            AuthUser(id="", email=email, password_hash=password_hash, name=name)
        )
        user = self._legacy.create(user)
        return to_auth_user(user)

    def update_user(self, user: AuthUser) -> AuthUser:
        return to_auth_user(self._legacy.update(to_provexa_user(user)))

    def store_password_reset_token(self, *, user_id: str, token_hash: str, expires_at: datetime) -> None:
        self._legacy.store_password_reset_token(token_hash, user_id, expires_at)

    def consume_password_reset_token(self, token_hash: str, now: datetime) -> AuthUser | None:
        user = self._legacy.consume_password_reset_token(token_hash)
        return to_auth_user(user) if user else None
