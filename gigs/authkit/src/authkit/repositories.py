from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .models import AuthUser, SessionPayload


class UserRepository(Protocol):
    """Abstraction over user persistence for AuthKit.

    Implementations adapt this protocol to concrete databases or ORMs.
    """

    def get_by_email(self, email: str) -> AuthUser | None: ...  # pragma: no cover - protocol

    def get_by_id(self, user_id: str) -> AuthUser | None: ...  # pragma: no cover - protocol

    def create(self, user: AuthUser) -> AuthUser: ...  # pragma: no cover - protocol

    def update(self, user: AuthUser) -> AuthUser: ...  # pragma: no cover - protocol

    def store_password_reset_token(self, token_hash: str, user_id: str, expires_at: datetime) -> None: ...  # pragma: no cover - protocol

    def consume_password_reset_token(self, token_hash: str) -> AuthUser | None: ...  # pragma: no cover - protocol

    def revoke_token(self, token_id: str, expires_at: datetime) -> None: ...  # pragma: no cover - protocol

    def is_token_revoked(self, token_id: str) -> bool: ...  # pragma: no cover - protocol


@dataclass(slots=True)
class SessionRecord:
    payload: SessionPayload


class SessionStore(Protocol):
    """Abstraction over server-side session storage.

    The canonical production implementation is Redis-backed; Batch 1 also
    defines an explicit in-memory variant for tests and local development.
    """

    def save(self, session: SessionPayload) -> None: ...  # pragma: no cover - protocol

    def get(self, token_id: str) -> SessionPayload | None: ...  # pragma: no cover - protocol

    def delete(self, token_id: str) -> None: ...  # pragma: no cover - protocol
