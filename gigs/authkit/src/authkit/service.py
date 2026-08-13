from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .config import AuthKitConfig
from .errors import AuthenticationError, ConflictError
from .models import AuthUser, TokenPair, TwoFactorSetup
from .passwords import hash_password, verify_password
from .repositories import UserRepository
from .sessions.base import SessionStore
from .tokens import (
    create_access_token,
    create_pending_2fa_token,
    decode_access_token,
    hash_opaque_token,
    new_opaque_token,
    token_ttl,
)
from .two_factor import generate_two_factor_secret, verify_totp_code


class AuthService:
    def __init__(self, repository: UserRepository, config: AuthKitConfig) -> None:
        config.validate()
        self._repository = repository
        self._config = config

    def signup(self, *, email: str, password: str, name: str | None = None) -> AuthUser:
        normalized_email = _normalize_email(email)
        if self._repository.get_by_email(normalized_email):
            raise ConflictError("User already exists", {"field": "email"})
        return self._repository.create_user(
            email=normalized_email,
            password_hash=hash_password(password, self._config),
            name=name.strip() if name else name,
        )

    def authenticate(self, *, email: str, password: str) -> AuthUser:
        user = self._repository.get_by_email(_normalize_email(email))
        if not user or not verify_password(password, user.password_hash, self._config):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        return user

    def login(
        self,
        *,
        email: str,
        password: str,
        session_store: SessionStore,
        claims: Mapping[str, Any] | None = None,
    ) -> TokenPair:
        user = self.authenticate(email=email, password=password)
        if user.two_factor_enabled:
            token = self.create_pending_2fa_login_token(user, session_store, claims)
            return TokenPair(token, requires_2fa=True)
        token = self.create_login_token(user, session_store, claims)
        return TokenPair(token)

    def create_login_token(
        self,
        user: AuthUser,
        session_store: SessionStore,
        claims: Mapping[str, Any] | None = None,
    ) -> str:
        token = create_access_token(str(user.id), self._config, {"email": user.email, **dict(claims or {})})
        self._store_token(token, user, session_store)
        return token

    def create_pending_2fa_login_token(
        self,
        user: AuthUser,
        session_store: SessionStore,
        claims: Mapping[str, Any] | None = None,
    ) -> str:
        token = create_pending_2fa_token(str(user.id), self._config, {"email": user.email, **dict(claims or {})})
        self._store_token(token, user, session_store)
        return token

    def logout(self, payload: Mapping[str, Any], session_store: SessionStore) -> None:
        session_id = payload.get("jti")
        if session_id:
            session_store.revoke(str(session_id), token_ttl(payload))

    def request_password_reset(self, *, email: str) -> str | None:
        user = self._repository.get_by_email(_normalize_email(email))
        if not user or not user.is_active:
            return None
        token = new_opaque_token()
        self._repository.store_password_reset_token(
            user_id=str(user.id),
            token_hash=hash_opaque_token(token, self._config),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=self._config.password_reset_token_minutes),
        )
        return token

    def reset_password(self, *, token: str, new_password: str) -> AuthUser:
        user = self._repository.consume_password_reset_token(
            hash_opaque_token(token, self._config), datetime.now(timezone.utc)
        )
        if not user:
            raise AuthenticationError("Invalid or expired password reset token")
        user.password_hash = hash_password(new_password, self._config)
        return self._repository.update_user(user)

    def begin_two_factor_setup(self, user: AuthUser) -> TwoFactorSetup:
        if user.two_factor_enabled:
            raise ConflictError("Two-factor authentication is already enabled")
        user.two_factor_secret = generate_two_factor_secret()
        self._repository.update_user(user)
        label = user.email.replace(":", "")
        uri = (
            f"otpauth://totp/{self._config.two_factor_issuer}:{label}"
            f"?secret={user.two_factor_secret}&issuer={self._config.two_factor_issuer}&digits=6"
        )
        return TwoFactorSetup(secret=user.two_factor_secret, provisioning_uri=uri)

    def verify_two_factor(self, user: AuthUser, code: str) -> AuthUser:
        if not user.two_factor_secret:
            raise AuthenticationError("Two-factor authentication is not configured")
        if not verify_totp_code(user.two_factor_secret, code):
            raise AuthenticationError("Invalid two-factor code")
        user.two_factor_enabled = True
        return self._repository.update_user(user)

    def _store_token(self, token: str, user: AuthUser, session_store: SessionStore) -> None:
        payload = decode_access_token(token, self._config)
        session_store.create(
            str(payload["jti"]),
            {
                "user_id": str(user.id),
                "jti": str(payload["jti"]),
                "purpose": payload.get("purpose"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
            },
            token_ttl(payload),
        )


def _normalize_email(email: str) -> str:
    return email.strip().lower()
