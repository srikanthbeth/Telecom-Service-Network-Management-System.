from datetime import datetime

from pydantic import BaseModel, ConfigDict


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