from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SLARuleCreate(BaseModel):
    rule_name: str = Field(
        min_length=3,
        max_length=150,
    )

    ticket_category: str | None = None

    priority: str | None = None

    customer_type: str | None = None

    sla_minutes: int = Field(
        gt=0,
    )

    warning_minutes: int = Field(
        default=60,
        ge=0,
    )

    escalation_enabled: bool = True

    is_active: bool = True


class SLARuleUpdate(BaseModel):
    rule_name: str | None = Field(
        default=None,
        min_length=3,
        max_length=150,
    )

    ticket_category: str | None = None

    priority: str | None = None

    customer_type: str | None = None

    sla_minutes: int | None = Field(
        default=None,
        gt=0,
    )

    warning_minutes: int | None = Field(
        default=None,
        ge=0,
    )

    escalation_enabled: bool | None = None

    is_active: bool | None = None


class SLARuleResponse(BaseModel):
    id: int
    rule_name: str
    ticket_category: str | None
    priority: str | None
    customer_type: str | None
    sla_minutes: int
    warning_minutes: int
    escalation_enabled: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class TicketSLAResponse(BaseModel):
    id: int
    ticket_id: int
    sla_rule_id: int
    start_time: datetime
    deadline: datetime
    resolution_time: datetime | None
    resolution_minutes: int | None
    status: str
    is_breached: bool
    escalation_status: str
    escalated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class SLAStatusResponse(BaseModel):
    ticket_id: int
    ticket_number: str
    status: str
    sla_status: str
    start_time: datetime
    deadline: datetime
    resolution_time: datetime | None
    resolution_minutes: int | None
    is_breached: bool
    escalation_status: str
    minutes_remaining: int | None