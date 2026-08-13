import unittest
from datetime import datetime, timezone

from authkit import AuthKitConfig, AuthService, AuthenticationError, ConflictError, InMemorySessionStore
from authkit.models import AuthUser
from authkit.passwords import verify_password
from authkit.two_factor import generate_totp_code


class FakeRepository:
    def __init__(self) -> None:
        self.users = {}
        self.reset_tokens = {}

    def get_by_email(self, email):
        return next((u for u in self.users.values() if u.email == email), None)

    def get_by_id(self, user_id):
        return self.users.get(user_id)

    def create_user(self, *, email, password_hash, name=None):
        user = AuthUser(str(len(self.users) + 1), email, password_hash, name, created_at=datetime.now(timezone.utc))
        self.users[user.id] = user
        return user

    def update_user(self, user):
        self.users[user.id] = user
        return user

    def store_password_reset_token(self, *, user_id, token_hash, expires_at):
        self.reset_tokens[token_hash] = (user_id, expires_at)

    def consume_password_reset_token(self, token_hash, now):
        item = self.reset_tokens.pop(token_hash, None)
        if not item or item[1] < now:
            return None
        return self.users.get(item[0])


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.config = AuthKitConfig(
            jwt_secret_key="service-secret", environment="test", allow_in_memory_sessions=True,
            expose_password_reset_token=True,
        )
        self.repository = FakeRepository()
        self.service = AuthService(self.repository, self.config)
        self.sessions = InMemorySessionStore(self.config)

    def test_signup_login_and_logout(self):
        user = self.service.signup(email=" User@Example.com ", password="strong-password", name=" Test ")
        self.assertEqual(user.email, "user@example.com")
        with self.assertRaises(ConflictError):
            self.service.signup(email="user@example.com", password="strong-password")
        pair = self.service.login(email="user@example.com", password="strong-password", session_store=self.sessions)
        self.assertFalse(pair.requires_2fa)
        self.assertEqual(len(self.sessions._sessions), 1)
        from authkit.tokens import decode_access_token

        payload = decode_access_token(pair.access_token, self.config)
        self.service.logout(payload, self.sessions)
        self.assertTrue(self.sessions.is_revoked(payload["jti"]))

    def test_password_reset_and_two_factor(self):
        user = self.service.signup(email="user@example.com", password="old-password")
        reset = self.service.request_password_reset(email="user@example.com")
        self.assertIsNotNone(reset)
        self.service.reset_password(token=reset, new_password="new-password")
        self.service.authenticate(email="user@example.com", password="new-password")

        setup = self.service.begin_two_factor_setup(user)
        self.assertTrue(setup.provisioning_uri.startswith("otpauth://totp/AuthKit:"))
        self.service.verify_two_factor(user, generate_totp_code(setup.secret))
        self.assertTrue(user.two_factor_enabled)
