from __future__ import annotations

import json
from typing import Any, Mapping

from ..config import AuthKitConfig
from ..errors import DependencyUnavailableError


class RedisSessionStore:
    mode = "redis"

    def __init__(self, client: Any, prefix: str) -> None:
        self._client = client
        self._prefix = prefix

    @classmethod
    def from_config(cls, config: AuthKitConfig) -> "RedisSessionStore":
        if not config.redis_url:
            raise DependencyUnavailableError("REDIS_URL is required because Redis is the session authority")
        try:
            import redis
        except Exception as exc:
            raise DependencyUnavailableError("Redis client dependency is unavailable") from exc
        try:
            client = redis.Redis.from_url(config.redis_url, decode_responses=True)
            client.ping()
        except Exception as exc:
            raise DependencyUnavailableError("Redis is unavailable for server-side sessions") from exc
        return cls(client, config.session_key_prefix)

    def _session_key(self, session_id: str) -> str:
        return f"{self._prefix}:session:{session_id}"

    def _revoked_key(self, session_id: str) -> str:
        return f"{self._prefix}:session-revoked:{session_id}"

    def ping(self) -> bool:
        return bool(self._client.ping())

    def create(self, session_id: str, payload: Mapping[str, Any], ttl_seconds: int) -> None:
        self._client.setex(self._session_key(session_id), max(1, int(ttl_seconds)), json.dumps(dict(payload)))

    def get(self, session_id: str) -> dict[str, Any] | None:
        raw = self._client.get(self._session_key(session_id))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        try:
            value = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def revoke(self, session_id: str, ttl_seconds: int) -> None:
        self._client.delete(self._session_key(session_id))
        self._client.setex(
            self._revoked_key(session_id), max(1, int(ttl_seconds)), json.dumps({"revoked": True})
        )

    def is_revoked(self, session_id: str) -> bool:
        return bool(self._client.exists(self._revoked_key(session_id)))
