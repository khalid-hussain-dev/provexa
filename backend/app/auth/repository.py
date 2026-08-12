from typing import Protocol
from datetime import datetime, timezone

from app.auth.models import User


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None: ...

    def get_by_id(self, user_id: str) -> User | None: ...

    def create(self, user: User) -> User: ...

    def update(self, user: User) -> User: ...

    def store_password_reset_token(self, token_hash: str, user_id: str, expires_at: datetime) -> None: ...

    def consume_password_reset_token(self, token_hash: str) -> User | None: ...

    def revoke_token(self, token_id: str, expires_at: datetime) -> None: ...

    def is_token_revoked(self, token_id: str) -> bool: ...


class InMemoryUserRepository:
    """Temporary auth store until the database foundation batch replaces it."""

    def __init__(self) -> None:
        self._users_by_email: dict[str, User] = {}
        self._users_by_id: dict[str, User] = {}
        self._password_reset_tokens: dict[str, tuple[str, datetime]] = {}
        self._revoked_tokens: dict[str, datetime] = {}

    def get_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email.lower())

    def get_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    def create(self, user: User) -> User:
        self._users_by_email[user.email.lower()] = user
        self._users_by_id[str(user.id)] = user
        return user

    def update(self, user: User) -> User:
        user.updated_at = datetime.now(timezone.utc)
        self._users_by_email[user.email.lower()] = user
        self._users_by_id[str(user.id)] = user
        return user

    def store_password_reset_token(self, token_hash: str, user_id: str, expires_at: datetime) -> None:
        self._password_reset_tokens[token_hash] = (user_id, expires_at)

    def consume_password_reset_token(self, token_hash: str) -> User | None:
        token_record = self._password_reset_tokens.pop(token_hash, None)
        if token_record is None:
            return None

        user_id, expires_at = token_record
        if expires_at < datetime.now(timezone.utc):
            return None
        return self.get_by_id(user_id)

    def revoke_token(self, token_id: str, expires_at: datetime) -> None:
        self._revoked_tokens[token_id] = expires_at

    def is_token_revoked(self, token_id: str) -> bool:
        expires_at = self._revoked_tokens.get(token_id)
        if expires_at is None:
            return False
        if expires_at < datetime.now(timezone.utc):
            self._revoked_tokens.pop(token_id, None)
            return False
        return True

    def clear(self) -> None:
        self._users_by_email.clear()
        self._users_by_id.clear()
        self._password_reset_tokens.clear()
        self._revoked_tokens.clear()


_user_repository = InMemoryUserRepository()


def get_user_repository() -> UserRepository:
    return _user_repository


def reset_user_repository() -> None:
    _user_repository.clear()
