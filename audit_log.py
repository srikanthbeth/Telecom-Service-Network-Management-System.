from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogCreate(BaseModel):
    user_id: int | None = None
    action: str
    entity: str
    entity_id: int | None = None
    previous_value: str | None = None
    new_value: str | None = None


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    entity: str
    entity_id: int | None
    timestamp: datetime
    previous_value: str | None
    new_value: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )