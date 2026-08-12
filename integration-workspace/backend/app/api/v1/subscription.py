from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database.session import get_db_session
from app.subscription.schemas import SubscriptionCheckoutRequest, SubscriptionCheckoutResponse, SubscriptionConfirmRequest, SubscriptionConfirmResponse
from app.subscription.service import SubscriptionService

router = APIRouter(prefix="/subscription", tags=["subscription"])


@router.post("/checkout", response_model=SubscriptionCheckoutResponse)
def checkout(
    payload: SubscriptionCheckoutRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> SubscriptionCheckoutResponse:
    record = SubscriptionService(session).checkout(str(current_user.id), payload.plan)
    return SubscriptionCheckoutResponse(checkout_id=UUID(str(record.id)))


@router.post("/confirm", response_model=SubscriptionConfirmResponse)
def confirm(
    payload: SubscriptionConfirmRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> SubscriptionConfirmResponse:
    SubscriptionService(session).confirm(str(current_user.id), str(payload.checkout_id))
    return SubscriptionConfirmResponse()

