import json
import unittest

from authkit import AuthKitConfig, DependencyUnavailableError, InMemorySessionStore, RedisSessionStore


class FakeRedis:
    def __init__(self) -> None:
        self.values = {}
        self.ttls = {}

    def ping(self):
        return True

    def setex(self, key, ttl, value):
        self.values[key] = value
        self.ttls[key] = ttl

    def get(self, key):
        return self.values.get(key)

    def delete(self, key):
        self.values.pop(key, None)

    def exists(self, key):
        return int(key in self.values)


class SessionTests(unittest.TestCase):
    def test_memory_store_requires_explicit_local_configuration(self) -> None:
        with self.assertRaises(DependencyUnavailableError):
            InMemorySessionStore(AuthKitConfig(jwt_secret_key="secret"))

    def test_memory_store_expires_and_revokes(self) -> None:
        now = [1000.0]
        config = AuthKitConfig(
            jwt_secret_key="secret", environment="test", allow_in_memory_sessions=True
        )
        store = InMemorySessionStore(config, clock=lambda: now[0])
        store.create("one", {"user_id": "u"}, 5)
        self.assertEqual(store.get("one"), {"user_id": "u"})
        now[0] = 1006
        self.assertIsNone(store.get("one"))
        store.revoke("two", 5)
        self.assertTrue(store.is_revoked("two"))
        now[0] = 1012
        self.assertFalse(store.is_revoked("two"))

    def test_redis_namespace_ttl_and_revocation(self) -> None:
        client = FakeRedis()
        store = RedisSessionStore(client, "authkit-test")
        store.create("one", {"user_id": "u"}, 10)
        self.assertEqual(store.get("one"), {"user_id": "u"})
        self.assertEqual(client.ttls["authkit-test:session:one"], 10)
        store.revoke("one", 10)
        self.assertIsNone(store.get("one"))
        self.assertTrue(store.is_revoked("one"))
        self.assertEqual(json.loads(client.values["authkit-test:session-revoked:one"]), {"revoked": True})
