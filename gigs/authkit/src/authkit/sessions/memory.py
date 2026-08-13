from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from ..models import SessionPayload
from ..repositories import SessionStore


class InMemorySessionStore(SessionStore):
    """Non-durable, process-local session store.

    This implementation is **intentionally** only for tests and ad-hoc local
    usage. To avoid accidental production use, construction requires an
    explicit flag acknowledging this limitation.
    """

    def __init__(self, *, allow_insecure: bool = False) -> None:
        if not allow_insecure:
            raise RuntimeError(
                "InMemorySessionStore is test-only and non-durable; "
                "pass allow_insecure=True to acknowledge this explicitly."
            )
        self._sessions: Dict[str, SessionPayload] = {}

    def save(self, session: SessionPayload) -> None:
        self._sessions[session.token_id] = session

    def get(self, token_id: str) -> SessionPayload | None:
        session = self._sessions.get(token_id)
        if not session:
            return None
        if session.expires_at < datetime.now(timezone.utc):
            self._sessions.pop(token_id, None)
            return None
        return session

    def delete(self, token_id: str) -> None:
        self._sessions.pop(token_id, None)
