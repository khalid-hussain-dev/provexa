from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from .config import AuthKitConfig
from .errors import AuthenticationError

_HEADER = {"alg": "HS256", "typ": "JWT"}


def create_access_token(
    subject: str,
    config: AuthKitConfig,
    claims: dict[str, Any] | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Create a signed JWT access token.

    Claims match the existing PROVEXA behavior:
    - ``sub``: subject (user id as string)
    - ``jti``: random token identifier
    - ``iat``: issued-at timestamp (seconds since epoch, UTC)
    - ``exp``: expiry timestamp (seconds since epoch, UTC)
    - optional ``purpose``: used for flows such as 2FA pending
    """

    now = datetime.now(timezone.utc)
    ttl = timedelta(minutes=expires_minutes or config.jwt_access_token_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "jti": secrets.token_urlsafe(16),
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    if claims:
        payload.update(claims)

    signing_input = f"{_b64_json(_HEADER)}.{_b64_json(payload)}"
    signature = _sign(signing_input, config.jwt_secret_key)
    return f"{signing_input}.{signature}"


def decode_access_token(token: str, config: AuthKitConfig) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Validates signature, ``exp`` (not in the past), and presence of ``sub``.
    Raises :class:`AuthenticationError` on any problem.
    """

    try:
        header_b64, payload_b64, signature = token.split(".")
    except ValueError as exc:
        raise AuthenticationError("Invalid access token") from exc

    signing_input = f"{header_b64}.{payload_b64}"
    expected_signature = _sign(signing_input, config.jwt_secret_key)
    if not hmac.compare_digest(signature, expected_signature):
        raise AuthenticationError("Invalid access token")

    try:
        payload = json.loads(_b64_decode(payload_b64))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthenticationError("Invalid access token") from exc

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(datetime.now(timezone.utc).timestamp()):
        raise AuthenticationError("Access token expired")
    if not payload.get("sub"):
        raise AuthenticationError("Invalid access token")
    return payload


def create_pending_2fa_token(subject: str, config: AuthKitConfig) -> str:
    """Create a short-lived token whose purpose is ``"2fa_pending"``."""

    return create_access_token(
        subject,
        config,
        {"purpose": "2fa_pending"},
        expires_minutes=config.pending_2fa_token_minutes,
    )


def require_token_purpose(payload: dict[str, Any], purpose: str) -> None:
    """Ensure a decoded token payload has the expected ``purpose`` claim."""

    if payload.get("purpose") != purpose:
        raise AuthenticationError("Invalid access token")


def hash_opaque_token(token: str, config: AuthKitConfig) -> str:
    """Hash an opaque token using HMAC-SHA256 and the JWT secret key."""

    digest = hmac.new(config.jwt_secret_key.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).digest()
    return _b64_encode(digest)


def new_opaque_token() -> str:
    """Generate a new random opaque token suitable for password reset flows."""

    return secrets.token_urlsafe(32)


def _b64_json(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _b64_encode(raw)


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _sign(signing_input: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return _b64_encode(digest)
