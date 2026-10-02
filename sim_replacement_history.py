from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SIMReplacementHistoryResponse(BaseModel):
    id: int
    old_sim_id: int
    new_sim_id: int
    customer_id: int
    reason: str | None
    replaced_by: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )