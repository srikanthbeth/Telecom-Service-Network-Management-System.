
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from utils.enums import EquipmentHealth, EquipmentType, NetworkStatus


class NetworkEquipment(Base):
    __tablename__ = "network_equipment"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    equipment_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    equipment_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    equipment_type: Mapped[EquipmentType] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    model_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    serial_number: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )

    tower_id: Mapped[int | None] = mapped_column(
        ForeignKey("towers.id"),
        nullable=True,
        index=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    installation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    maintenance_schedule: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    cpu_usage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    memory_usage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    network_status: Mapped[NetworkStatus] = mapped_column(
        String(50),
        default=NetworkStatus.ONLINE.value,
        nullable=False,
        index=True,
    )

    health_status: Mapped[EquipmentHealth] = mapped_column(
        String(50),
        default=EquipmentHealth.HEALTHY.value,
        nullable=False,
        index=True,
    )

    last_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    downtime_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    tower = relationship(
        "Tower",
        backref="network_equipment",
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by],
    )
