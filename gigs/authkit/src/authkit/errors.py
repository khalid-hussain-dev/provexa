from __future__ import annotations

from typing import Any


class AuthKitError(Exception):
    code = "AUTHKIT_ERROR"
    status_code = 400

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(AuthKitError):
    code = "AUTHENTICATION_ERROR"
    status_code = 401


class AuthorizationError(AuthKitError):
    code = "AUTHORIZATION_ERROR"
    status_code = 403


class ConflictError(AuthKitError):
    code = "CONFLICT"
    status_code = 409


class ValidationError(AuthKitError):
    code = "VALIDATION_ERROR"
    status_code = 422


class DependencyUnavailableError(AuthKitError):
    code = "DEPENDENCY_UNAVAILABLE"
    status_code = 503


def error_envelope(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}
