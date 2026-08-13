from __future__ import annotations

from ..config import AuthKitConfig
from ..errors import DependencyUnavailableError
from .base import SessionStore
from .memory import InMemorySessionStore
from .redis import RedisSessionStore


def build_session_store(config: AuthKitConfig) -> SessionStore:
    config.validate()
    if config.redis_url:
        return RedisSessionStore.from_config(config)
    if config.allow_in_memory_sessions:
        return InMemorySessionStore(config)
    raise DependencyUnavailableError("REDIS_URL is required for production server-side sessions")


__all__ = ["SessionStore", "InMemorySessionStore", "RedisSessionStore", "build_session_store"]
