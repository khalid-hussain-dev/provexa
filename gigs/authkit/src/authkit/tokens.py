from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .config import AuthKitConfig
from .errors import AuthenticationError

_HEADER = {"alg": "HS256", "typ": "JWT"}


def create_access_token(
    subject: str,
    config: AuthKitConfig,
    claims: Mapping[str, Any] | None = None,
    expires_minutes: int | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    minutes = expires_minutes if expires_minutes is not None else config.jwt_access_token_minutes
    payload: dict[str, Any] = {
        "sub": subject,
        "jti": secrets.token_urlsafe(16),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
    }
    if claims:
        payload.update(dict(claims))
    signing_input = f"{_b64_json(_HEADER)}.{_b64_json(payload)}"
    return f"{signing_input}.{_sign(signing_input, config.jwt_secret_key)}"


def create_pending_2fa_token(
    subject: str,
    config: AuthKitConfig,
    claims: Mapping[str, Any] | None = None,
) -> str:
    merged = dict(claims or {})
    merged["purpose"] = "2fa_pending"
    return create_access_token(subject, config, merged, config.pending_2fa_token_minutes)


def decode_access_token(token: str, config: AuthKitConfig) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"
        expected_signature = _sign(signing_input, config.jwt_secret_key)
        if not hmac.compare_digest(signature, expected_signature):
            raise AuthenticationError("Invalid access token")
        header = json.loads(_b64_decode(header_b64))
        if not isinstance(header, dict) or header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise AuthenticationError("Invalid access token")
        payload = json.loads(_b64_decode(payload_b64))
    except AuthenticationError:
        raise
    except (ValueError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuthenticationError("Invalid access token") from exc

    if not isinstance(payload, dict):
        raise AuthenticationError("Invalid access token")
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        raise AuthenticationError("Access token expired")
    if not payload.get("sub"):
        raise AuthenticationError("Invalid access token")
    return payload


def require_token_purpose(payload: Mapping[str, Any], purpose: str) -> None:
    if payload.get("purpose") != purpose:
        raise AuthenticationError("Invalid access token")


def token_ttl(payload: Mapping[str, Any], now: int | None = None) -> int:
    current = int(time.time()) if now is None else now
    try:
        return max(1, int(payload["exp"]) - current)
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError("Invalid access token") from exc


def hash_opaque_token(token: str, config: AuthKitConfig) -> str:
    digest = hmac.new(config.jwt_secret_key.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).digest()
    return _b64_encode(digest)


def new_opaque_token() -> str:
    return secrets.token_urlsafe(32)


def _b64_json(value: dict[str, Any]) -> str:
    return _b64_encode(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _sign(signing_input: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return _b64_encode(digest)
