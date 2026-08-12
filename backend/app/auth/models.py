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
    name: str | None = None
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    two_factor_enabled: bool = False
    two_factor_secret: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, email: str, password_hash: str, name: str | None = None) -> "User":
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            name=name,
            is_active=True,
            two_factor_enabled=False,
            two_factor_secret=None,
            created_at=now,
            updated_at=now,
        )
