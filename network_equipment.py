
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import EquipmentHealth, EquipmentType, NetworkStatus


class NetworkEquipmentCreate(BaseModel):
    equipment_code: str = Field(
        min_length=2,
        max_length=50,
    )

    equipment_name: str = Field(
        min_length=2,
        max_length=150,
    )

    equipment_type: EquipmentType

    manufacturer: str | None = Field(
        default=None,
        max_length=100,
    )

    model_number: str | None = Field(
        default=None,
        max_length=100,
    )

    serial_number: str | None = Field(
        default=None,
        max_length=100,
    )

    tower_id: int | None = Field(
        default=None,
        gt=0,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    installation_date: date | None = None

    maintenance_schedule: date | None = None

    cpu_usage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    memory_usage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    network_status: NetworkStatus = NetworkStatus.ONLINE

    health_status: EquipmentHealth = EquipmentHealth.HEALTHY

    last_heartbeat: datetime | None = None

    downtime_minutes: int = Field(
        default=0,
        ge=0,
    )

    description: str | None = None


class NetworkEquipmentUpdate(BaseModel):
    equipment_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    equipment_type: EquipmentType | None = None

    manufacturer: str | None = Field(
        default=None,
        max_length=100,
    )

    model_number: str | None = Field(
        default=None,
        max_length=100,
    )

    serial_number: str | None = Field(
        default=None,
        max_length=100,
    )

    tower_id: int | None = Field(
        default=None,
        gt=0,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    installation_date: date | None = None

    maintenance_schedule: date | None = None

    cpu_usage: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    memory_usage: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    last_heartbeat: datetime | None = None

    downtime_minutes: int | None = Field(
        default=None,
        ge=0,
    )

    description: str | None = None


class NetworkEquipmentStatusUpdate(BaseModel):
    network_status: NetworkStatus


class NetworkEquipmentHealthUpdate(BaseModel):
    health_status: EquipmentHealth


class NetworkEquipmentResponse(BaseModel):
    id: int
    equipment_code: str
    equipment_name: str
    equipment_type: EquipmentType
    manufacturer: str | None
    model_number: str | None
    serial_number: str | None
    tower_id: int | None
    location: str | None
    installation_date: date | None
    maintenance_schedule: date | None
    cpu_usage: float
    memory_usage: float
    network_status: NetworkStatus
    health_status: EquipmentHealth
    last_heartbeat: datetime | None
    downtime_minutes: int
    description: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

