from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import OutageSeverity


class NetworkOutageCreate(BaseModel):
    outage_code: str = Field(
        min_length=2,
        max_length=50,
    )

    outage_type: str = Field(
        min_length=2,
        max_length=100,
    )

    description: str | None = None

    severity: OutageSeverity

    start_time: datetime

    expected_resolution: datetime | None = None

    tower_ids: list[int] = Field(
        min_length=1,
    )


class NetworkOutageUpdate(BaseModel):
    outage_type: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    description: str | None = None

    severity: OutageSeverity | None = None

    start_time: datetime | None = None

    expected_resolution: datetime | None = None


class NetworkOutageResolve(BaseModel):
    actual_resolution: datetime | None = None


class TowerResponse(BaseModel):
    id: int
    tower_code: str
    tower_name: str
    tower_type: str
    latitude: float
    longitude: float
    status: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class AffectedCustomerResponse(BaseModel):
    customer_id: int


class NetworkOutageResponse(BaseModel):
    id: int
    outage_code: str
    outage_type: str
    description: str | None
    severity: OutageSeverity
    start_time: datetime
    expected_resolution: datetime | None
    actual_resolution: datetime | None
    created_at: datetime
    updated_at: datetime

    tower_ids: list[int] = []
    affected_customer_ids: list[int] = []