from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AuthUser:
    id: str
    email: str
    password_hash: str
    name: str | None = None
    is_active: bool = True
    two_factor_enabled: bool = False
    two_factor_secret: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    token_type: str = "bearer"
    requires_2fa: bool = False


@dataclass(frozen=True)
class SessionPayload:
    user_id: str
    jti: str
    issued_at: int
    expires_at: int
    purpose: str | None = None


@dataclass(frozen=True)
class TwoFactorSetup:
    secret: str
    provisioning_uri: str
