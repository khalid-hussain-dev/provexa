import unittest
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from authkit import AuthKitConfig, AuthService, AuthUser, InMemorySessionStore
from authkit.fastapi import create_auth_router, register_authkit_error_handler


class MemoryRepository:
    def __init__(self):
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


class FastAPIIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.config = AuthKitConfig(
            jwt_secret_key="fastapi-test-secret",
            environment="test",
            allow_in_memory_sessions=True,
            expose_password_reset_token=True,
        )
        self.repository = MemoryRepository()
        self.sessions = InMemorySessionStore(self.config)
        self.app = FastAPI()
        register_authkit_error_handler(self.app)
        self.app.include_router(
            create_auth_router(
                repository_provider=lambda request: self.repository,
                config_provider=lambda request: self.config,
                session_store_provider=lambda request: self.sessions,
                service_provider=lambda request: AuthService(self.repository, self.config),
            )
        )
        self.client = TestClient(self.app)

    def test_auth_flow_and_error_envelope(self):
        signup = self.client.post(
            "/auth/signup",
            json={"name": "Test User", "email": "USER@example.com", "password": "strong-password"},
        )
        self.assertEqual(signup.status_code, 201)
        login = self.client.post(
            "/auth/login", json={"email": "user@example.com", "password": "strong-password"}
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["access_token"]
        me = self.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["email"], "user@example.com")
        logout = self.client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(logout.status_code, 200)
        blocked = self.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(blocked.status_code, 401)
        self.assertEqual(blocked.json()["error"]["code"], "AUTHENTICATION_ERROR")

    def test_validation_and_duplicate_signup(self):
        weak = self.client.post("/auth/signup", json={"email": "user@example.com", "password": "short"})
        self.assertEqual(weak.status_code, 422)
        self.client.post("/auth/signup", json={"email": "user@example.com", "password": "strong-password"})
        duplicate = self.client.post(
            "/auth/signup", json={"email": "user@example.com", "password": "strong-password"}
        )
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.json()["error"]["code"], "CONFLICT")
