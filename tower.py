from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.tower import TowerStatus, TowerType


class TowerCreate(BaseModel):
    tower_code: str = Field(
        min_length=1,
        max_length=100,
    )

    tower_name: str = Field(
        min_length=1,
        max_length=150,
    )

    tower_type: TowerType

    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )

    address: str | None = None

    coverage_area: float = Field(
        gt=0,
    )

    capacity: int = Field(
        gt=0,
    )

    status: TowerStatus = TowerStatus.ACTIVE


class TowerUpdate(BaseModel):
    tower_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    tower_type: TowerType | None = None

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    address: str | None = None

    coverage_area: float | None = Field(
        default=None,
        gt=0,
    )

    capacity: int | None = Field(
        default=None,
        gt=0,
    )

    status: TowerStatus | None = None


class TowerStatusUpdate(BaseModel):
    status: TowerStatus


class TowerResponse(BaseModel):
    id: int
    tower_code: str
    tower_name: str
    tower_type: TowerType
    latitude: float
    longitude: float
    address: str | None
    coverage_area: float
    capacity: int
    status: TowerStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )