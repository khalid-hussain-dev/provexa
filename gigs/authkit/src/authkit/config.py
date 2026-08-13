from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthKitConfig:
    """Application configuration for AuthKit.

    Memory sessions are deliberately opt-in and accepted only in local/test
    environments. Production-like applications must provide Redis.
    """

    jwt_secret_key: str
    jwt_access_token_minutes: int = 30
    pending_2fa_token_minutes: int = 5
    password_reset_token_minutes: int = 30
    password_algorithm: str = "pbkdf2_sha256"
    password_iterations: int = 260_000
    password_salt_bytes: int = 16
    redis_url: str | None = None
    session_key_prefix: str = "authkit"
    allow_in_memory_sessions: bool = False
    environment: str = "production"
    two_factor_issuer: str = "AuthKit"
    expose_password_reset_token: bool = False

    @property
    def is_local_or_test(self) -> bool:
        return self.environment.strip().lower() in {"development", "dev", "test", "testing"}

    def validate(self) -> None:
        if not self.jwt_secret_key:
            raise ValueError("jwt_secret_key is required")
        if self.jwt_access_token_minutes < 1 or self.pending_2fa_token_minutes < 1:
            raise ValueError("token lifetimes must be positive")
        if self.password_iterations < 1 or self.password_salt_bytes < 1:
            raise ValueError("password parameters must be positive")
        if self.allow_in_memory_sessions and not self.is_local_or_test:
            raise ValueError("in-memory sessions are allowed only in local/test environments")
        if self.expose_password_reset_token and not self.is_local_or_test:
            raise ValueError("password reset tokens may be exposed only in local/test environments")
