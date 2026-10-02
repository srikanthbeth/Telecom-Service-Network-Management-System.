from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import SIMStatus, SIMType


class SIMCreate(BaseModel):
    sim_number: str = Field(
        min_length=5,
        max_length=50,
    )

    sim_type: SIMType

    customer_id: int | None = Field(
        default=None,
        gt=0,
    )

    plan_id: int | None = Field(
        default=None,
        gt=0,
    )

    tower_id: int | None = Field(
        default=None,
        gt=0,
    )


class SIMUpdate(BaseModel):
    sim_number: str | None = Field(
        default=None,
        min_length=5,
        max_length=50,
    )

    sim_type: SIMType | None = None

    customer_id: int | None = Field(
        default=None,
        gt=0,
    )

    plan_id: int | None = Field(
        default=None,
        gt=0,
    )

    tower_id: int | None = Field(
        default=None,
        gt=0,
    )


class SIMResponse(BaseModel):
    id: int
    sim_number: str
    sim_type: SIMType
    status: SIMStatus
    activation_date: date | None
    customer_id: int | None
    plan_id: int | None
    tower_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class SIMReplaceRequest(BaseModel):
    new_sim_id: int = Field(
        gt=0
    )

    reason: str | None = Field(
        default=None,
        max_length=500,
    )