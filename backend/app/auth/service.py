from app.auth.models import User
from datetime import datetime, timezone

from app.auth.passwords import hash_password, verify_password
from app.auth.two_factor import generate_two_factor_secret, verify_totp_code
from app.auth.repository import UserRepository
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
        user.updated_at = datetime.now(timezone.utc)
        return user.two_factor_secret

    def verify_two_factor(self, user: User, code: str) -> User:
        if not user.two_factor_secret:
            raise AuthenticationError("Two-factor authentication is not configured")
        if not verify_totp_code(user.two_factor_secret, code):
            raise AuthenticationError("Invalid two-factor code")
        user.two_factor_enabled = True
        user.updated_at = datetime.now(timezone.utc)
        return user

    def simulate_forgot_password(self, email: str) -> None:
        # Intentionally do not reveal whether the email exists.
        return None
