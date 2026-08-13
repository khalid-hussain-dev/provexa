from __future__ import annotations

import hashlib
import hmac
import secrets

from .config import AuthKitConfig

_ALGORITHM = "pbkdf2_sha256"


def hash_password(password: str, config: AuthKitConfig | None = None) -> str:
    cfg = config or AuthKitConfig(jwt_secret_key="local-password-only")
    if cfg.password_algorithm != _ALGORITHM:
        raise ValueError(f"unsupported password algorithm: {cfg.password_algorithm}")
    salt = secrets.token_hex(cfg.password_salt_bytes)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), cfg.password_iterations
    )
    return f"{_ALGORITHM}${cfg.password_iterations}${salt}${digest.hex()}"


def verify_password(
    password: str,
    password_hash: str,
    config: AuthKitConfig | None = None,
) -> bool:
    try:
        algorithm, iterations_text, salt, expected = password_hash.split("$", 3)
        if algorithm != _ALGORITHM:
            return False
        iterations = int(iterations_text)
        if iterations < 1 or not salt or not expected:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return hmac.compare_digest(digest.hex(), expected)
    except (TypeError, ValueError, UnicodeError):
        return False
