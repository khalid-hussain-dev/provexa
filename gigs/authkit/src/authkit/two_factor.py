from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass

from .config import AuthKitConfig
from .models import TwoFactorSetup

_CODE_DIGITS = 6
_TIME_STEP_SECONDS = 30


def generate_two_factor_secret() -> str:
    """Generate a random base32-encoded shared secret for TOTP."""

    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def generate_totp_code(secret: str, for_time: int | None = None) -> str:
    timestamp = int(time.time()) if for_time is None else for_time
    counter = timestamp // _TIME_STEP_SECONDS
    key = _decode_secret(secret)
    digest = hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = int.from_bytes(digest[offset : offset + 4], "big") & 0x7FFFFFFF
    return str(value % (10**_CODE_DIGITS)).zfill(_CODE_DIGITS)


def verify_totp_code(secret: str, code: str, at_time: int | None = None, window: int = 1) -> bool:
    normalized = code.strip()
    if not normalized.isdigit() or len(normalized) != _CODE_DIGITS:
        return False

    now = int(time.time()) if at_time is None else at_time
    for step in range(-window, window + 1):
        candidate_time = now + (step * _TIME_STEP_SECONDS)
        if hmac.compare_digest(generate_totp_code(secret, candidate_time), normalized):
            return True
    return False


def begin_two_factor_setup(user_id: str, secret: str | None, config: AuthKitConfig, email: str) -> TwoFactorSetup:
    """Prepare a new 2FA setup flow.

    The caller is responsible for persisting the generated secret against the
    user. This helper simply returns the secret and provisioning URI.
    """

    if secret is None:
        secret = generate_two_factor_secret()

    label = f"{config.two_factor_issuer}:{email}"
    provisioning_uri = f"otpauth://totp/{label}?secret={secret}&issuer={config.two_factor_issuer}"
    return TwoFactorSetup(secret=secret, provisioning_uri=provisioning_uri)


def _decode_secret(secret: str) -> bytes:
    padding = "=" * (-len(secret) % 8)
    return base64.b32decode(f"{secret}{padding}", casefold=True)
