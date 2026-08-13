from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from authkit import (
    AuthKitConfig,
    AuthenticationError,
    create_access_token,
    create_pending_2fa_token,
    decode_access_token,
    hash_opaque_token,
    hash_password,
    new_opaque_token,
    require_token_purpose,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    raw = "strong-password"
    hashed = hash_password(raw)

    assert hashed.startswith("pbkdf2_sha256$260000$")
    assert verify_password(raw, hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_creation_and_decoding_roundtrip() -> None:
    config = AuthKitConfig(jwt_secret_key="secret", jwt_access_token_minutes=5)
    token = create_access_token("user-id", config, {"purpose": "access"})

    payload = decode_access_token(token, config)
    assert payload["sub"] == "user-id"
    assert payload["purpose"] == "access"
    assert isinstance(payload["iat"], int)
    assert isinstance(payload["exp"], int)


def test_jwt_expiry_is_enforced() -> None:
    config = AuthKitConfig(jwt_secret_key="secret", jwt_access_token_minutes=-1)
    token = create_access_token("user-id", config)

    with pytest.raises(AuthenticationError):
        decode_access_token(token, config)


def test_pending_2fa_token_has_purpose() -> None:
    config = AuthKitConfig(jwt_secret_key="secret", pending_2fa_token_minutes=1)
    token = create_pending_2fa_token("user-id", config)
    payload = decode_access_token(token, config)

    require_token_purpose(payload, "2fa_pending")


def test_require_token_purpose_rejects_mismatch() -> None:
    config = AuthKitConfig(jwt_secret_key="secret")
    token = create_access_token("user-id", config, {"purpose": "other"})
    payload = decode_access_token(token, config)

    with pytest.raises(AuthenticationError):
        require_token_purpose(payload, "2fa_pending")


def test_opaque_token_hash_changes_with_secret() -> None:
    config1 = AuthKitConfig(jwt_secret_key="secret1")
    config2 = AuthKitConfig(jwt_secret_key="secret2")

    token = new_opaque_token()
    h1 = hash_opaque_token(token, config1)
    h2 = hash_opaque_token(token, config2)

    assert h1 != h2
