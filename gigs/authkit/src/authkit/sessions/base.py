from __future__ import annotations

from typing import Any, Mapping, Protocol


class SessionStore(Protocol):
    mode: str

    def ping(self) -> bool: ...

    def create(self, session_id: str, payload: Mapping[str, Any], ttl_seconds: int) -> None: ...

    def get(self, session_id: str) -> dict[str, Any] | None: ...

    def revoke(self, session_id: str, ttl_seconds: int) -> None: ...

    def is_revoked(self, session_id: str) -> bool: ...
