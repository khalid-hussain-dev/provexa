from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any

# Redis is an optional dependency; importing this module will fail if it is not
# installed, but the rest of AuthKit core does not depend on it.
try:  # pragma: no cover - import guard
    import redis  # type: ignore[import]
except Exception as exc:  # pragma: no cover - import guard
    raise RuntimeError("redis extra is required to use RedisSessionStore") from exc

from ..models import SessionPayload
from ..repositories import SessionStore


class RedisSessionStore(SessionStore):
    """Redis-backed implementation of :class:`SessionStore`.

    Stores sessions as JSON blobs under keys derived from the token id, with
    Redis key expiry aligned to the session's ``expires_at``.
    """

    def __init__(self, client: "redis.Redis[Any]") -> None:
        self._client = client

    @staticmethod
    def _key(token_id: str) -> str:
        return f"authkit:session:{token_id}"

    def save(self, session: SessionPayload) -> None:
        payload = {
            "user_id": session.user_id,
            "token_id": session.token_id,
            "issued_at": session.issued_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "purpose": session.purpose,
            "extra": session.extra or {},
        }
        ttl_seconds = max(0, int((session.expires_at - datetime.now(timezone.utc)).total_seconds()))
        self._client.set(self._key(session.token_id), json.dumps(payload), ex=ttl_seconds)

    def get(self, token_id: str) -> SessionPayload | None:
        raw = self._client.get(self._key(token_id))
        if raw is None:
            return None
        data = json.loads(raw)
        session = SessionPayload(
            user_id=str(data["user_id"]),
            token_id=str(data["token_id"]),
            issued_at=datetime.fromisoformat(data["issued_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            purpose=data.get("purpose"),
            extra=data.get("extra") or {},
        )
        if session.expires_at < datetime.now(timezone.utc):
            self.delete(token_id)
            return None
        return session

    def delete(self, token_id: str) -> None:
        self._client.delete(self._key(token_id))
