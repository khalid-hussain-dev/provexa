from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(slots=True)
class AuthUser:
    """Framework-independent user view used by AuthKit.

    Concrete applications are free to adapt their persistence model to this
    representation via the :class:`UserRepository` protocol.
    """

    id: UUID
    email: str
    password_hash: str
    name: str | None = None
    is_active: bool = True
    two_factor_enabled: bool = False
    two_factor_secret: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, email: str, password_hash: str, name: str | None = None) -> "AuthUser":
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            name=name,
            is_active=True,
            two_factor_enabled=False,
            two_factor_secret=None,
            created_at=now,
            updated_at=now,
        )


@dataclass(slots=True)
class TokenPair:
    """Minimal token pair representation.

    Batch 1 uses only access tokens; refresh or other token types can be added
    later without breaking this shape by keeping fields optional.
    """

    access_token: str
    refresh_token: str | None = None


@dataclass(slots=True)
class SessionPayload:
    """Information stored in a server-side session store.

    This is intentionally small and derived from JWT claims.
    """

    user_id: str
    token_id: str
    issued_at: datetime
    expires_at: datetime
    purpose: str | None = None
    extra: dict[str, Any] | None = None


@dataclass(slots=True)
class TwoFactorSetup:
    """Information returned when beginning 2FA setup."""

    secret: str
    provisioning_uri: str
