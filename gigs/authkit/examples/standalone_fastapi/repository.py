from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from authkit import AuthUser


class ExampleUserRepository:
    def __init__(self) -> None:
        self.users: dict[str, AuthUser] = {}
        self.reset_tokens: dict[str, tuple[str, datetime]] = {}

    def get_by_email(self, email: str) -> AuthUser | None:
        return next((u for u in self.users.values() if u.email == email), None)

    def get_by_id(self, user_id: str) -> AuthUser | None:
        return self.users.get(user_id)

    def create_user(self, *, email: str, password_hash: str, name: str | None = None) -> AuthUser:
        user = AuthUser(id=str(uuid4()), email=email, password_hash=password_hash, name=name, created_at=datetime.now(timezone.utc))
        self.users[user.id] = user
        return user

    def update_user(self, user: AuthUser) -> AuthUser:
        user.updated_at = datetime.now(timezone.utc)
        self.users[user.id] = user
        return user

    def store_password_reset_token(self, *, user_id: str, token_hash: str, expires_at: datetime) -> None:
        self.reset_tokens[token_hash] = (user_id, expires_at)

    def consume_password_reset_token(self, token_hash: str, now: datetime) -> AuthUser | None:
        item = self.reset_tokens.pop(token_hash, None)
        if not item or item[1] < now:
            return None
        return self.users.get(item[0])
