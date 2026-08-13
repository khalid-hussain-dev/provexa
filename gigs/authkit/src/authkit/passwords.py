from __future__ import annotations

import hashlib
import hmac
import secrets

# These constants are chosen to match PROVEXA's existing password format.
_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 260_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256.

    The output format is strictly:

        pbkdf2_sha256$260000$<salt_hex>$<digest_hex>
    """

    salt = secrets.token_hex(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS)
    return f"{_ALGORITHM}${_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored hash.

    Returns ``False`` on any parsing error or algorithm mismatch.
    """

    try:
        algorithm, iterations, salt, expected = password_hash.split("$", 3)
        if algorithm != _ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False
