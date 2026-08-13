from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .models import AuthUser


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> AuthUser | None: ...

    def get_by_id(self, user_id: str) -> AuthUser | None: ...

    def create_user(self, *, email: str, password_hash: str, name: str | None = None) -> AuthUser: ...

    def update_user(self, user: AuthUser) -> AuthUser: ...

    def store_password_reset_token(self, *, user_id: str, token_hash: str, expires_at: datetime) -> None: ...

    def consume_password_reset_token(self, token_hash: str, now: datetime) -> AuthUser | None: ...
