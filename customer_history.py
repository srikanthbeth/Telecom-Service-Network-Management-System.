from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CustomerHistoryResponse(BaseModel):
    id: int
    customer_id: int
    changed_by: int
    action: str
    description: str | None
    previous_value: dict | None
    new_value: dict | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )