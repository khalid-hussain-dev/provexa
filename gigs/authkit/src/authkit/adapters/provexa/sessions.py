from __future__ import annotations

from typing import Any, Mapping

from ...sessions.base import SessionStore


class ProvexaSessionStore:
    """Delegating facade over the existing integration SessionStore."""

    def __init__(self, legacy_store: SessionStore) -> None:
        self._legacy = legacy_store
        self.mode = legacy_store.mode

    def ping(self) -> bool:
        return self._legacy.ping()

    def create(self, session_id: str, payload: Mapping[str, Any], ttl_seconds: int) -> None:
        self._legacy.create(session_id, dict(payload), ttl_seconds)

    def get(self, session_id: str) -> dict[str, Any] | None:
        return self._legacy.get(session_id)

    def revoke(self, session_id: str, ttl_seconds: int) -> None:
        self._legacy.revoke(session_id, ttl_seconds)

    def is_revoked(self, session_id: str) -> bool:
        return self._legacy.is_revoked(session_id)


def build_provexa_session_store() -> ProvexaSessionStore:
    from integration.session_store import build_session_store

    return ProvexaSessionStore(build_session_store())
