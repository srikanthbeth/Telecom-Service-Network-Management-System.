from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import SubscriptionStatus


class SubscriptionCreate(BaseModel):
    customer_id: int = Field(gt=0)
    sim_id: int = Field(gt=0)
    plan_id: int = Field(gt=0)
    start_date: date
    end_date: date


class SubscriptionPlanChange(BaseModel):
    plan_id: int = Field(gt=0)


class SubscriptionRenew(BaseModel):
    end_date: date


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    customer_id: int
    sim_id: int
    plan_id: int
    start_date: date
    end_date: date
    status: SubscriptionStatus
    created_at: datetime
    updated_at: datetime


class SubscriptionHistoryResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    subscription_id: int
    action: str
    previous_plan_id: int | None
    new_plan_id: int | None
    previous_status: str | None
    new_status: str | None
    description: str | None
    changed_by: int | None
    created_at: datetime