from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import (
    TechnicianAvailability,
    TechnicianJobStatus,
)


class TechnicianCreate(BaseModel):
    user_id: int

    employee_id: str = Field(
        min_length=2,
        max_length=50,
    )

    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    phone: str = Field(
        min_length=5,
        max_length=30,
    )

    availability: TechnicianAvailability = (
        TechnicianAvailability.AVAILABLE
    )

    latitude: float | None = None
    longitude: float | None = None

    service_area: str | None = Field(
        default=None,
        max_length=255,
    )

    address: str | None = None


class TechnicianUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    phone: str | None = Field(
        default=None,
        min_length=5,
        max_length=30,
    )

    availability: TechnicianAvailability | None = None

    latitude: float | None = None
    longitude: float | None = None

    service_area: str | None = Field(
        default=None,
        max_length=255,
    )

    address: str | None = None


class TechnicianSkillCreate(BaseModel):
    skill_name: str = Field(
        min_length=2,
        max_length=100,
    )


class TechnicianSkillResponse(BaseModel):
    id: int
    technician_id: int
    skill_name: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class TechnicianResponse(BaseModel):
    id: int
    user_id: int
    employee_id: str
    full_name: str
    phone: str
    availability: TechnicianAvailability
    latitude: float | None
    longitude: float | None
    service_area: str | None
    address: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class TechnicianAssignmentCreate(BaseModel):
    technician_id: int

    customer_id: int | None = None

    job_type: str = Field(
        min_length=2,
        max_length=100,
    )

    job_reference_id: int | None = None

    description: str | None = None


class TechnicianReassignment(BaseModel):
    technician_id: int


class TechnicianAssignmentStatusUpdate(BaseModel):
    status: TechnicianJobStatus


class TechnicianAssignmentResponse(BaseModel):
    id: int
    technician_id: int
    customer_id: int | None
    job_type: str
    job_reference_id: int | None
    description: str | None
    status: TechnicianJobStatus
    assigned_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    notes: str | None
    assigned_by: int | None

    model_config = ConfigDict(
        from_attributes=True,
    )