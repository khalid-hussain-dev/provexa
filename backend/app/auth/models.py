from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(slots=True)
class User:
    """Persistence-ready user domain model.

    This model is intentionally storage-agnostic for the current in-memory
    repository and can be mapped to database persistence in a later batch.
    """

    email: str
    password_hash: str
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, email: str, password_hash: str) -> "User":
        return cls(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
