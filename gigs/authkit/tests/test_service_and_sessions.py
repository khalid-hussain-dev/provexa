from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from authkit import (
    AuthKitConfig,
    AuthService,
    AuthUser,
    AuthenticationError,
    ConflictError,
    SessionPayload,
)
from authkit.repositories import SessionStore, UserRepository
from authkit.sessions import InMemorySessionStore


class InMemoryUserRepo(UserRepository):
    def __init__(self) -> None:
        self._users: dict[str, AuthUser] = {}
        self._reset_tokens: dict[str, tuple[str, datetime]] = {}
        self._revoked: set[str] = set()

    def get_by_email(self, email: str) -> AuthUser | None:
        return next((u for u in self._users.values() if u.email == email), None)

    def get_by_id(self, user_id: str) -> AuthUser | None:
        return self._users.get(str(user_id))

    def create(self, user: AuthUser) -> AuthUser:
        self._users[str(user.id)] = user
        return user

    def update(self, user: AuthUser) -> AuthUser:
        self._users[str(user.id)] = user
        return user

    def store_password_reset_token(self, token_hash: str, user_id: str, expires_at: datetime) -> None:
        self._reset_tokens[token_hash] = (user_id, expires_at)

    def consume_password_reset_token(self, token_hash: str) -> AuthUser | None:
        record = self._reset_tokens.pop(token_hash, None)
        if not record:
            return None
        user_id, expires_at = record
        if expires_at < datetime.now(timezone.utc):
            return None
        return self.get_by_id(user_id)

    def revoke_token(self, token_id: str, expires_at: datetime) -> None:  # pragma: no cover - not used in Batch 1
        self._revoked.add(token_id)

    def is_token_revoked(self, token_id: str) -> bool:  # pragma: no cover - not used in Batch 1
        return token_id in self._revoked


def test_signup_and_authenticate_flow() -> None:
    repo = InMemoryUserRepo()
    service = AuthService(repo)

    user = service.signup("User@Example.com", "strong-password", name="Khalid")
    assert user.id

    with pytest.raises(ConflictError):
        service.signup("User@Example.com", "other")

    authed = service.authenticate("User@Example.com", "strong-password")
    assert authed.id == user.id

    with pytest.raises(AuthenticationError):
        service.authenticate("User@Example.com", "wrong")


def test_password_reset_flow() -> None:
    repo = InMemoryUserRepo()
    service = AuthService(repo)
    config = AuthKitConfig(jwt_secret_key="secret", password_reset_token_minutes=1)

    user = service.signup("user@example.com", "old-password")

    token = service.request_password_reset("user@example.com", config)
    assert token is not None

    # Unregistered email gives no token but succeeds silently
    assert service.request_password_reset("missing@example.com", config) is None

    updated = service.reset_password(token, "new-password", config)  # type: ignore[arg-type]
    assert updated.id == user.id

    # Reusing the token fails
    with pytest.raises(AuthenticationError):
        service.reset_password(token, "another", config)  # type: ignore[arg-type]


def test_password_reset_token_respects_expiry() -> None:
    repo = InMemoryUserRepo()
    service = AuthService(repo)
    config = AuthKitConfig(jwt_secret_key="secret", password_reset_token_minutes=-1)

    user = service.signup("user@example.com", "old-password")
    token = service.request_password_reset("user@example.com", config)
    assert token is not None

    with pytest.raises(AuthenticationError):
        service.reset_password(token, "new-password", config)  # type: ignore[arg-type]


def test_two_factor_verification() -> None:
    from authkit.two_factor import generate_two_factor_secret, generate_totp_code

    repo = InMemoryUserRepo()
    service = AuthService(repo)

    user = service.signup("user@example.com", "password")
    user.two_factor_secret = generate_two_factor_secret()
    repo.update(user)

    code = generate_totp_code(user.two_factor_secret)
    verified = service.verify_two_factor(user, code)
    assert verified.two_factor_enabled is True

    with pytest.raises(AuthenticationError):
        service.verify_two_factor(user, "000000")


def test_in_memory_session_store_requires_explicit_flag() -> None:
    with pytest.raises(RuntimeError):
        InMemorySessionStore()

    store = InMemorySessionStore(allow_insecure=True)
    now = datetime.now(timezone.utc)
    payload = SessionPayload(
        user_id=str(uuid4()),
        token_id="token",
        issued_at=now,
        expires_at=now + timedelta(seconds=1),
        purpose=None,
        extra=None,
    )

    store.save(payload)
    assert store.get("token") is not None

    # Force expiry
    payload.expires_at = now - timedelta(seconds=1)
    store.save(payload)

    assert store.get("token") is None
    store.delete("token")
