from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import DeviceStatus, DeviceType


class DeviceCreate(BaseModel):
    imei: str = Field(
        min_length=15,
        max_length=20,
    )
    model: str = Field(
        min_length=1,
        max_length=150,
    )
    manufacturer: str = Field(
        min_length=1,
        max_length=150,
    )
    device_type: DeviceType
    customer_id: int | None = Field(
        default=None,
        gt=0,
    )


class DeviceUpdate(BaseModel):
    imei: str | None = Field(
        default=None,
        min_length=15,
        max_length=20,
    )
    model: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    manufacturer: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    device_type: DeviceType | None = None
    customer_id: int | None = Field(
        default=None,
        gt=0,
    )


class DeviceResponse(BaseModel):
    id: int
    imei: str
    model: str
    manufacturer: str
    device_type: DeviceType
    status: DeviceStatus
    customer_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class DeviceSIMAssignRequest(BaseModel):
    sim_id: int = Field(
        gt=0,
    )


class DeviceSIMMappingResponse(BaseModel):
    id: int
    device_id: int
    sim_id: int
    is_active: bool
    assigned_at: datetime
    unassigned_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )