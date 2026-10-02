from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import (
    ServiceRequestStatus,
    ServiceRequestType,
)


class ServiceRequestCreate(BaseModel):
    customer_id: int

    request_type: ServiceRequestType

    reason: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = None


class ServiceRequestStatusUpdate(BaseModel):
    status: ServiceRequestStatus

    remarks: str | None = Field(
        default=None,
        max_length=500,
    )


class ServiceRequestResponse(BaseModel):
    id: int
    request_number: str
    customer_id: int
    request_type: ServiceRequestType
    status: ServiceRequestStatus
    reason: str | None
    description: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ServiceRequestHistoryResponse(BaseModel):
    id: int
    service_request_id: int
    old_status: ServiceRequestStatus | None
    new_status: ServiceRequestStatus
    remarks: str | None
    changed_by: int
    changed_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )