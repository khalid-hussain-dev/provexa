from __future__ import annotations

import json
import os
import time
from threading import RLock
from typing import Any, Protocol

from .errors import DependencyUnavailableError
from .runtime import allow_in_memory_sessions

try:
    import redis  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - exercised through unavailable-dependency tests
    redis = None


class SessionStore(Protocol):
    mode: str

    def ping(self) -> bool: ...

    def create(self, session_id: str, payload: dict[str, Any], ttl_seconds: int) -> None: ...

    def get(self, session_id: str) -> dict[str, Any] | None: ...

    def revoke(self, session_id: str, ttl_seconds: int) -> None: ...

    def is_revoked(self, session_id: str) -> bool: ...


class InMemorySessionStore:
    """Explicitly non-production session store for local development/tests only."""

    mode = "memory-local-only"

    def __init__(self) -> None:
        self._sessions: dict[str, tuple[float, dict[str, Any]]] = {}
        self._revoked: dict[str, float] = {}
        self._lock = RLock()

    def ping(self) -> bool:
        return True

    def create(self, session_id: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        with self._lock:
            self._sessions[session_id] = (time.time() + max(1, ttl_seconds), dict(payload))

    def get(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            item = self._sessions.get(session_id)
            if item is None:
                return None
            expires_at, payload = item
            if expires_at <= time.time():
                self._sessions.pop(session_id, None)
                return None
            return dict(payload)

    def revoke(self, session_id: str, ttl_seconds: int) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
            self._revoked[session_id] = time.time() + max(1, ttl_seconds)

    def is_revoked(self, session_id: str) -> bool:
        with self._lock:
            expires_at = self._revoked.get(session_id)
            if expires_at is None:
                return False
            if expires_at <= time.time():
                self._revoked.pop(session_id, None)
                return False
            return True


class RedisSessionStore:
    mode = "redis"

    def __init__(self, client: Any, prefix: str) -> None:
        self._client = client
        self._prefix = prefix

    def _session_key(self, session_id: str) -> str:
        return f"{self._prefix}:session:{session_id}"

    def _revoked_key(self, session_id: str) -> str:
        return f"{self._prefix}:session-revoked:{session_id}"

    def ping(self) -> bool:
        return bool(self._client.ping())

    def create(self, session_id: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        self._client.setex(self._session_key(session_id), max(1, ttl_seconds), json.dumps(payload))

    def get(self, session_id: str) -> dict[str, Any] | None:
        raw = self._client.get(self._session_key(session_id))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        value = json.loads(raw)
        return value if isinstance(value, dict) else None

    def revoke(self, session_id: str, ttl_seconds: int) -> None:
        self._client.delete(self._session_key(session_id))
        self._client.setex(
            self._revoked_key(session_id),
            max(1, ttl_seconds),
            json.dumps({"revoked": True}),
        )

    def is_revoked(self, session_id: str) -> bool:
        return bool(self._client.exists(self._revoked_key(session_id)))


def build_session_store() -> SessionStore:
    redis_url = os.getenv("REDIS_URL", "").strip()
    prefix = os.getenv("TRANSIENT_STATE_PREFIX", "provexa").strip() or "provexa"
    if not redis_url:
        if allow_in_memory_sessions():
            return InMemorySessionStore()
        raise DependencyUnavailableError(
            "REDIS_URL is required because Redis is the server-side session authority"
        )

    if redis is None:
        if allow_in_memory_sessions():
            return InMemorySessionStore()
        raise DependencyUnavailableError("Redis client dependency is unavailable")

    timeout = float(os.getenv("REDIS_CONNECT_TIMEOUT_SECONDS", "1"))
    try:
        client = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
        )
        client.ping()
    except Exception as exc:
        if allow_in_memory_sessions():
            return InMemorySessionStore()
        raise DependencyUnavailableError("Redis is unavailable for server-side sessions") from exc
    return RedisSessionStore(client, prefix)

