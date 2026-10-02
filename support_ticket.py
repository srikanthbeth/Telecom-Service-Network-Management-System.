from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)


class SupportTicketCreate(BaseModel):
    customer_id: int

    category: TicketCategory

    subject: str = Field(
        min_length=3,
        max_length=200,
    )

    description: str = Field(
        min_length=5,
    )

    priority: TicketPriority = TicketPriority.MEDIUM


class SupportTicketUpdate(BaseModel):
    category: TicketCategory | None = None

    subject: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = None

    priority: TicketPriority | None = None


class TicketStatusUpdate(BaseModel):
    status: TicketStatus

    resolution_notes: str | None = None


class TicketAgentAssignment(BaseModel):
    agent_id: int


class TicketTechnicianAssignment(BaseModel):
    technician_id: int


class TicketReassignment(BaseModel):
    agent_id: int | None = None
    technician_id: int | None = None


class TicketEscalation(BaseModel):
    escalation_level: int = Field(
        ge=1,
        le=10,
    )

    reason: str | None = None


class TicketCommentCreate(BaseModel):
    comment: str = Field(
        min_length=1,
        max_length=5000,
    )


class TicketCommentResponse(BaseModel):
    id: int
    ticket_id: int
    author_id: int
    comment: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class TicketHistoryResponse(BaseModel):
    id: int
    ticket_id: int
    action: str
    old_value: str | None
    new_value: str | None
    changed_by: int | None
    description: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class SupportTicketResponse(BaseModel):
    id: int
    ticket_number: str
    customer_id: int
    category: TicketCategory
    subject: str
    description: str
    priority: TicketPriority
    status: TicketStatus

    assigned_agent_id: int | None
    assigned_technician_id: int | None

    escalation_level: int
    is_escalated: bool

    resolution_notes: str | None

    resolved_at: datetime | None
    closed_at: datetime | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )