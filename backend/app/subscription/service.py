from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.database.models import SubscriptionRecord
from app.core.errors import NotFoundError

ALLOWED_PLANS = {"FREE", "PRO", "ENTERPRISE"}


class SubscriptionService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def checkout(self, user_id: str, plan: str) -> SubscriptionRecord:
        normalized = plan.upper()
        if normalized not in ALLOWED_PLANS:
            raise ValueError("invalid plan")

        record = SubscriptionRecord(
            id=str(uuid4()),
            user_id=user_id,
            plan=normalized,
            status="PENDING",
            provider="demo",
            external_reference=f"demo-checkout-{uuid4().hex[:12]}",
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def confirm(self, user_id: str, checkout_id: str) -> SubscriptionRecord:
        record = self._session.get(SubscriptionRecord, checkout_id)
        if record is None or record.user_id != user_id:
            raise NotFoundError("Checkout not found", {"checkout_id": checkout_id})
        record.status = "ACTIVE"
        record.external_reference = record.external_reference or f"demo-payment-{checkout_id}"
        self._session.commit()
        self._session.refresh(record)
        return record
