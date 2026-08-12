from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Protocol

from app.core.config import Settings, get_settings

try:
    import redis  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency fallback
    redis = None


class TransientCache(Protocol):
    mode: str

    def ping(self) -> bool: ...

    def get_json(self, key: str) -> Any | None: ...

    def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None: ...

    def delete(self, key: str) -> None: ...


@dataclass
class CacheHealth:
    mode: str
    ready: bool


class InMemoryTransientCache:
    mode = "memory"

    def __init__(self, prefix: str = "provexa") -> None:
        self._prefix = prefix
        self._store: dict[str, tuple[datetime | None, str]] = {}

    def _key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def ping(self) -> bool:
        return True

    def get_json(self, key: str) -> Any | None:
        payload = self._store.get(self._key(key))
        if payload is None:
            return None
        expires_at, value = payload
        if expires_at is not None and expires_at < datetime.now(timezone.utc):
            self.delete(key)
            return None
        return json.loads(value)

    def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        self._store[self._key(key)] = (expires_at, json.dumps(value))

    def delete(self, key: str) -> None:
        self._store.pop(self._key(key), None)


class RedisTransientCache:
    mode = "redis"

    def __init__(self, client: Any, prefix: str = "provexa") -> None:
        self._client = client
        self._prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def ping(self) -> bool:
        return bool(self._client.ping())

    def get_json(self, key: str) -> Any | None:
        raw = self._client.get(self._key(key))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        payload = json.dumps(value)
        if ttl_seconds is None:
            self._client.set(self._key(key), payload)
        else:
            self._client.setex(self._key(key), ttl_seconds, payload)

    def delete(self, key: str) -> None:
        self._client.delete(self._key(key))


@lru_cache
def get_transient_cache() -> TransientCache:
    settings = get_settings()
    if settings.redis_url and redis is not None:
        try:
            client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=settings.redis_connect_timeout_seconds,
                socket_timeout=settings.redis_connect_timeout_seconds,
            )
            client.ping()
            return RedisTransientCache(client, prefix=settings.transient_state_prefix)
        except Exception:
            return InMemoryTransientCache(prefix=f"{settings.transient_state_prefix}:fallback")
    return InMemoryTransientCache(prefix=settings.transient_state_prefix)


def get_cache_health() -> CacheHealth:
    cache = get_transient_cache()
    return CacheHealth(mode=cache.mode, ready=cache.ping())


def reset_transient_cache() -> None:
    get_transient_cache.cache_clear()
