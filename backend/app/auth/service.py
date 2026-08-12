from app.auth.models import User
from app.auth.passwords import hash_password, verify_password
from app.auth.repository import UserRepository
from app.core.errors import AuthenticationError, ConflictError


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def signup(self, email: str, password: str) -> User:
        if self._repository.get_by_email(email):
            raise ConflictError("User already exists", {"field": "email"})
        user = User.create(email=email, password_hash=hash_password(password))
        return self._repository.create(user)

    def authenticate(self, email: str, password: str) -> User:
        user = self._repository.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        return user
