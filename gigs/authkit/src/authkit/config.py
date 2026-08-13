from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(slots=True)
class AuthKitConfig:
    """Configuration for AuthKit core.

    This stays intentionally small for Batch 1 and mirrors the semantics of the
    existing PROVEXA settings where relevant, without importing them.
    """

    # Symmetric signing key for JWTs and opaque token hashing.
    jwt_secret_key: str

    # Access token lifetime in minutes.
    jwt_access_token_minutes: int = 60

    # Lifetime for temporary 2FA "pending" tokens.
    pending_2fa_token_minutes: int = 5

    # Lifetime for password reset opaque tokens.
    password_reset_token_minutes: int = 30

    # Default 2FA issuer label for provisioning URIs (standalone default).
    two_factor_issuer: str = "AuthKit"

    @property
    def access_token_ttl(self) -> timedelta:
        return timedelta(minutes=self.jwt_access_token_minutes)

    @property
    def pending_2fa_ttl(self) -> timedelta:
        return timedelta(minutes=self.pending_2fa_token_minutes)

    @property
    def password_reset_ttl(self) -> timedelta:
        return timedelta(minutes=self.password_reset_token_minutes)
