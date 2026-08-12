from typing import Protocol
from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database.models import PasswordResetTokenRecord, RevokedTokenRecord, UserRecord
from app.database.session import SessionLocal, get_db_session, init_database
from app.auth.models import User


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None: ...

    def get_by_id(self, user_id: str) -> User | None: ...

    def create(self, user: User) -> User: ...

    def update(self, user: User) -> User: ...

    def store_password_reset_token(self, token_hash: str, user_id: str, expires_at: datetime) -> None: ...

    def consume_password_reset_token(self, token_hash: str) -> User | None: ...

    def revoke_token(self, token_id: str, expires_at: datetime) -> None: ...

    def is_token_revoked(self, token_id: str) -> bool: ...


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_email(self, email: str) -> User | None:
        record = self._session.scalar(select(UserRecord).where(UserRecord.email == email.lower()))
        return _to_user(record) if record else None

    def get_by_id(self, user_id: str) -> User | None:
        record = self._session.get(UserRecord, user_id)
        return _to_user(record) if record else None

    def create(self, user: User) -> User:
        record = UserRecord(
            id=str(user.id),
            name=user.name,
            email=user.email.lower(),
            password_hash=user.password_hash,
            two_factor_enabled=user.two_factor_enabled,
            two_factor_secret=user.two_factor_secret,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return user

    def update(self, user: User) -> User:
        user.updated_at = datetime.now(timezone.utc)
        record = self._session.get(UserRecord, str(user.id))
        if record is None:
            record = UserRecord(id=str(user.id), email=user.email.lower(), password_hash=user.password_hash)
            self._session.add(record)
        record.name = user.name
        record.email = user.email.lower()
        record.password_hash = user.password_hash
        record.two_factor_enabled = user.two_factor_enabled
        record.two_factor_secret = user.two_factor_secret
        record.is_active = user.is_active
        record.updated_at = user.updated_at
        self._session.commit()
        return user

    def store_password_reset_token(self, token_hash: str, user_id: str, expires_at: datetime) -> None:
        self._session.merge(PasswordResetTokenRecord(token_hash=token_hash, user_id=user_id, expires_at=expires_at))
        self._session.commit()

    def consume_password_reset_token(self, token_hash: str) -> User | None:
        record = self._session.get(PasswordResetTokenRecord, token_hash)
        if record is None:
            return None

        user_id = record.user_id
        expires_at = _aware(record.expires_at)
        self._session.delete(record)
        self._session.commit()
        if expires_at < datetime.now(timezone.utc):
            return None
        return self.get_by_id(user_id)

    def revoke_token(self, token_id: str, expires_at: datetime) -> None:
        self._session.merge(RevokedTokenRecord(token_id=token_id, expires_at=expires_at))
        self._session.commit()

    def is_token_revoked(self, token_id: str) -> bool:
        record = self._session.get(RevokedTokenRecord, token_id)
        if record is None:
            return False
        expires_at = _aware(record.expires_at)
        if expires_at < datetime.now(timezone.utc):
            self._session.delete(record)
            self._session.commit()
            return False
        return True


def _to_user(record: UserRecord) -> User:
    return User(
        id=UUID(str(record.id)),
        name=record.name,
        email=record.email,
        password_hash=record.password_hash,
        two_factor_enabled=record.two_factor_enabled,
        two_factor_secret=record.two_factor_secret,
        is_active=record.is_active,
        created_at=_aware(record.created_at),
        updated_at=_aware(record.updated_at),
    )


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def get_user_repository(session: Session = Depends(get_db_session)) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def reset_user_repository() -> None:
    init_database()
    with SessionLocal() as session:
        session.execute(delete(PasswordResetTokenRecord))
        session.execute(delete(RevokedTokenRecord))
        session.execute(delete(UserRecord))
        session.commit()
