import unittest

from authkit import (
    AuthKitConfig,
    AuthenticationError,
    create_access_token,
    create_pending_2fa_token,
    decode_access_token,
    require_token_purpose,
)


class TokenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = AuthKitConfig(jwt_secret_key="test-secret", environment="test")

    def test_claims_and_purpose(self) -> None:
        token = create_access_token("user-1", self.config, {"email": "user@example.com"})
        payload = decode_access_token(token, self.config)
        self.assertEqual(payload["sub"], "user-1")
        self.assertIn("jti", payload)
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)
        self.assertNotIn("purpose", payload)

        pending = decode_access_token(create_pending_2fa_token("user-1", self.config), self.config)
        self.assertEqual(pending["purpose"], "2fa_pending")

    def test_tampering_and_expiry_fail(self) -> None:
        token = create_access_token("user-1", self.config)
        header, payload, signature = token.split(".")
        with self.assertRaises(AuthenticationError):
            decode_access_token(f"{header}.{payload}.bad", self.config)
        expired = create_access_token("user-1", self.config, expires_minutes=-1)
        with self.assertRaises(AuthenticationError):
            decode_access_token(expired, self.config)

    def test_purpose_enforcement(self) -> None:
        with self.assertRaises(AuthenticationError):
            require_token_purpose({}, "2fa_pending")
