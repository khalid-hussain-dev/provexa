from datetime import datetime, timedelta, timezone

from app.auth.models import User
from app.auth.passwords import hash_password, verify_password
from app.auth.repository import UserRepository
from app.auth.tokens import hash_opaque_token, new_opaque_token
from app.auth.two_factor import generate_two_factor_secret, verify_totp_code
from app.core.config import Settings
from app.core.errors import AuthenticationError, ConflictError


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def signup(self, email: str, password: str, name: str | None = None) -> User:
        if self._repository.get_by_email(email):
            raise ConflictError("User already exists", {"field": "email"})
        user = User.create(email=email, password_hash=hash_password(password), name=name)
        return self._repository.create(user)

    def authenticate(self, email: str, password: str) -> User:
        user = self._repository.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        return user

    def begin_two_factor_setup(self, user: User) -> str:
        if user.two_factor_enabled:
            raise ConflictError("Two-factor authentication is already enabled")
        user.two_factor_secret = generate_two_factor_secret()
        self._repository.update(user)
        return user.two_factor_secret

    def verify_two_factor(self, user: User, code: str) -> User:
        if not user.two_factor_secret:
            raise AuthenticationError("Two-factor authentication is not configured")
        if not verify_totp_code(user.two_factor_secret, code):
            raise AuthenticationError("Invalid two-factor code")
        user.two_factor_enabled = True
        return self._repository.update(user)

    def request_password_reset(self, email: str, settings: Settings) -> str | None:
        user = self._repository.get_by_email(email)
        if not user or not user.is_active:
            return None

        token = new_opaque_token()
        token_hash = hash_opaque_token(token, settings)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_token_minutes)
        self._repository.store_password_reset_token(token_hash, str(user.id), expires_at)
        return token

    def reset_password(self, token: str, new_password: str, settings: Settings) -> User:
        token_hash = hash_opaque_token(token, settings)
        user = self._repository.consume_password_reset_token(token_hash)
        if not user:
            raise AuthenticationError("Invalid or expired password reset token")
        user.password_hash = hash_password(new_password)
        return self._repository.update(user)
