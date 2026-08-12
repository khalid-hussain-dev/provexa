from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SubscriptionCheckoutRequest(BaseModel):
    plan: str = Field(min_length=1, max_length=32)

    @field_validator("plan")
    @classmethod
    def normalize_plan(cls, value: str) -> str:
        return value.strip().upper()


class SubscriptionCheckoutResponse(BaseModel):
    checkout_id: UUID
    status: str = "PENDING"


class SubscriptionConfirmRequest(BaseModel):
    checkout_id: UUID


class SubscriptionConfirmResponse(BaseModel):
    status: str = "ACTIVE"
    demo_payment: bool = True

