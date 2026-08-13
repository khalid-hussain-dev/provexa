from __future__ import annotations


class AuthKitError(Exception):
    """Base class for all AuthKit-specific errors."""


class AuthenticationError(AuthKitError):
    """Raised when credentials, tokens, or sessions are invalid."""


class ConflictError(AuthKitError):
    """Raised when attempting an operation that violates uniqueness or state.

    For example, signing up with an existing email or enabling 2FA twice.
    """

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field
