from typing import Protocol

from app.auth.models import User


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None: ...

    def get_by_id(self, user_id: str) -> User | None: ...

    def create(self, user: User) -> User: ...


class InMemoryUserRepository:
    """Temporary auth store until the database foundation batch replaces it."""

    def __init__(self) -> None:
        self._users_by_email: dict[str, User] = {}
        self._users_by_id: dict[str, User] = {}

    def get_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email.lower())

    def get_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    def create(self, user: User) -> User:
        self._users_by_email[user.email.lower()] = user
        self._users_by_id[str(user.id)] = user
        return user

    def clear(self) -> None:
        self._users_by_email.clear()
        self._users_by_id.clear()


_user_repository = InMemoryUserRepository()


def get_user_repository() -> UserRepository:
    return _user_repository


def reset_user_repository() -> None:
    _user_repository.clear()
