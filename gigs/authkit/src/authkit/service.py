from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .config import AuthKitConfig
from .errors import AuthenticationError, ConflictError
from .jwt import hash_opaque_token, new_opaque_token
from .models import AuthUser
from .passwords import hash_password, verify_password
from .repositories import UserRepository
from .two_factor import verify_totp_code


class AuthService:
    """Core authentication behavior.

    This service intentionally focuses on user signup, credential-based
    authentication, password reset, and 2FA verification helpers.
    Session handling and HTTP concerns live elsewhere.
    """

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    # --- Signup & login -------------------------------------------------

    def signup(self, email: str, password: str, name: str | None = None) -> AuthUser:
        if self._repository.get_by_email(email):
            raise ConflictError("User already exists", field="email")
        user = AuthUser.create(email=email, password_hash=hash_password(password), name=name)
        return self._repository.create(user)

    def authenticate(self, email: str, password: str) -> AuthUser:
        user = self._repository.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        return user

    # --- Two-factor helpers --------------------------------------------

    def verify_two_factor(self, user: AuthUser, code: str) -> AuthUser:
        if not user.two_factor_secret:
            raise AuthenticationError("Two-factor authentication is not configured")
        if not verify_totp_code(user.two_factor_secret, code):
            raise AuthenticationError("Invalid two-factor code")
        user.two_factor_enabled = True
        return self._repository.update(user)

    # --- Password reset -------------------------------------------------

    def request_password_reset(self, email: str, config: AuthKitConfig) -> str | None:
        """Initiate password reset.

        Returns a plain reset token when a matching active user exists; returns
        ``None`` otherwise without disclosing account existence.
        """

        user = self._repository.get_by_email(email)
        if not user or not user.is_active:
            return None

        token = new_opaque_token()
        token_hash = hash_opaque_token(token, config)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=config.password_reset_token_minutes)
        self._repository.store_password_reset_token(token_hash, str(user.id), expires_at)
        return token

    def reset_password(self, token: str, new_password: str, config: AuthKitConfig) -> AuthUser:
        token_hash = hash_opaque_token(token, config)
        user = self._repository.consume_password_reset_token(token_hash)
        if not user:
            raise AuthenticationError("Invalid or expired password reset token")
        user.password_hash = hash_password(new_password)
        return self._repository.update(user)
