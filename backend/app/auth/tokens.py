import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import Settings
from app.core.errors import AuthenticationError

_HEADER = {"alg": "HS256", "typ": "JWT"}


def create_access_token(
    subject: str,
    settings: Settings,
    claims: dict[str, Any] | None = None,
    expires_minutes: int | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes or settings.jwt_access_token_minutes)).timestamp()),
    }
    if claims:
        payload.update(claims)

    signing_input = f"{_b64_json(_HEADER)}.{_b64_json(payload)}"
    signature = _sign(signing_input, settings.jwt_secret_key)
    return f"{signing_input}.{signature}"


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature = token.split(".")
    except ValueError as exc:
        raise AuthenticationError("Invalid access token") from exc

    signing_input = f"{header_b64}.{payload_b64}"
    expected_signature = _sign(signing_input, settings.jwt_secret_key)
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


def create_pending_2fa_token(subject: str, settings: Settings) -> str:
    return create_access_token(subject, settings, {"purpose": "2fa_pending"}, expires_minutes=5)


def require_token_purpose(payload: dict[str, Any], purpose: str) -> None:
    if payload.get("purpose") != purpose:
        raise AuthenticationError("Invalid access token")


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
