from __future__ import annotations

import json


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expiries: dict[str, int] = {}

    def ping(self) -> bool:
        return True

    def setex(self, key: str, ttl: int, value: str) -> None:
        self.values[key] = value
        self.expiries[key] = ttl

    def get(self, key: str):
        return self.values.get(key)

    def delete(self, key: str) -> None:
        self.values.pop(key, None)

    def exists(self, key: str) -> int:
        return int(key in self.values)


def test_redis_session_store_namespaces_identity_expiry_and_revocation() -> None:
    from integration.session_store import RedisSessionStore

    client = FakeRedis()
    store = RedisSessionStore(client, "provexa-test")
    store.create("session-id", {"user_id": "user-id"}, 120)

    assert store.ping() is True
    assert store.get("session-id") == {"user_id": "user-id"}
    assert client.expiries["provexa-test:session:session-id"] == 120

    store.revoke("session-id", 120)

    assert store.get("session-id") is None
    assert store.is_revoked("session-id") is True
    assert "provexa-test:session-revoked:session-id" in client.values
    assert json.loads(client.values["provexa-test:session-revoked:session-id"])["revoked"] is True


def test_in_memory_sessions_expire(monkeypatch) -> None:
    import integration.session_store as session_module
    from integration.session_store import InMemorySessionStore

    store = InMemorySessionStore()
    now = 1000.0
    monkeypatch.setattr(session_module.time, "time", lambda: now)
    store.create("session-id", {"user_id": "user-id"}, 5)
    assert store.get("session-id") == {"user_id": "user-id"}

    monkeypatch.setattr(session_module.time, "time", lambda: now + 6)
    assert store.get("session-id") is None


def test_production_like_runtime_fails_without_redis(monkeypatch) -> None:
    import integration.session_store as session_module
    from integration.errors import DependencyUnavailableError

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("REDIS_URL", "redis://unavailable.invalid/0")
    monkeypatch.delenv("INTEGRATION_ALLOW_INMEMORY_SESSIONS", raising=False)
    monkeypatch.setattr(session_module, "redis", None)

    try:
        session_module.build_session_store()
    except DependencyUnavailableError as exc:
        assert "Redis" in exc.message
    else:
        raise AssertionError("Production-like startup must not silently fall back to memory")

