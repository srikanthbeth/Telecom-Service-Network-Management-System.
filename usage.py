from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import UsageType


class UsageCreate(BaseModel):
    customer_id: int = Field(
        gt=0
    )

    sim_id: int = Field(
        gt=0
    )

    subscription_id: int = Field(
        gt=0
    )

    usage_type: UsageType

    usage_date: date

    quantity: float = Field(
        gt=0
    )


class UsageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    customer_id: int
    sim_id: int
    subscription_id: int
    usage_type: UsageType
    usage_date: date
    quantity: float
    created_at: datetime


class UsageSummaryResponse(BaseModel):
    customer_id: int
    sim_id: int
    subscription_id: int

    data_usage_mb: float
    voice_usage_minutes: float
    sms_usage: float

    total_records: int


class UsageUtilizationResponse(BaseModel):
    customer_id: int
    sim_id: int
    subscription_id: int
    plan_id: int

    data_used_mb: float
    data_limit_mb: float
    data_percentage: float
    data_remaining_mb: float

    voice_used_minutes: float
    voice_limit_minutes: float
    voice_percentage: float
    voice_remaining_minutes: float

    sms_used: float
    sms_limit: float
    sms_percentage: float
    sms_remaining: float