from __future__ import annotations

import time
from threading import RLock
from typing import Any, Callable, Mapping

from ..config import AuthKitConfig
from ..errors import DependencyUnavailableError


class InMemorySessionStore:
    mode = "memory-local-only"

    def __init__(self, config: AuthKitConfig, clock: Callable[[], float] | None = None) -> None:
        if not config.allow_in_memory_sessions or not config.is_local_or_test:
            raise DependencyUnavailableError("in-memory sessions require explicit local/test configuration")
        self._clock = clock or time.time
        self._sessions: dict[str, tuple[float, dict[str, Any]]] = {}
        self._revoked: dict[str, float] = {}
        self._lock = RLock()

    def ping(self) -> bool:
        return True

    def create(self, session_id: str, payload: Mapping[str, Any], ttl_seconds: int) -> None:
        with self._lock:
            self._sessions[session_id] = (self._clock() + max(1, int(ttl_seconds)), dict(payload))

    def get(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            item = self._sessions.get(session_id)
            if item is None:
                return None
            expires_at, payload = item
            if expires_at <= self._clock():
                self._sessions.pop(session_id, None)
                return None
            return dict(payload)

    def revoke(self, session_id: str, ttl_seconds: int) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
            self._revoked[session_id] = self._clock() + max(1, int(ttl_seconds))

    def is_revoked(self, session_id: str) -> bool:
        with self._lock:
            expires_at = self._revoked.get(session_id)
            if expires_at is None:
                return False
            if expires_at <= self._clock():
                self._revoked.pop(session_id, None)
                return False
            return True
