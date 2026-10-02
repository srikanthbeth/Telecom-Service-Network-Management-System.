from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import PlanStatus, PlanType


class PlanCreate(BaseModel):
    plan_name: str = Field(
        min_length=3,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    plan_type: PlanType

    validity_days: int = Field(
        gt=0,
        le=3650,
    )

    data_limit_mb: int = Field(
        default=0,
        ge=0,
    )

    voice_limit_minutes: int = Field(
        default=0,
        ge=0,
    )

    sms_limit: int = Field(
        default=0,
        ge=0,
    )

    price: float = Field(
        gt=0,
    )


class PlanUpdate(BaseModel):
    plan_name: str | None = Field(
        default=None,
        min_length=3,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    plan_type: PlanType | None = None

    validity_days: int | None = Field(
        default=None,
        gt=0,
        le=3650,
    )

    data_limit_mb: int | None = Field(
        default=None,
        ge=0,
    )

    voice_limit_minutes: int | None = Field(
        default=None,
        ge=0,
    )

    sms_limit: int | None = Field(
        default=None,
        ge=0,
    )

    price: float | None = Field(
        default=None,
        gt=0,
    )


class PlanResponse(BaseModel):
    id: int
    plan_name: str
    description: str | None
    plan_type: PlanType
    validity_days: int
    data_limit_mb: int
    voice_limit_minutes: int
    sms_limit: int
    price: float
    status: PlanStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class PlanComparisonResponse(BaseModel):
    id: int
    plan_name: str
    plan_type: PlanType
    validity_days: int
    data_limit_mb: int
    voice_limit_minutes: int
    sms_limit: int
    price: float
    status: PlanStatus

    model_config = ConfigDict(
        from_attributes=True
    )