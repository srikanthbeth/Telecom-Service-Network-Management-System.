from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class TowerType(str, Enum):
    MACRO = "Macro"
    MICRO = "Micro"
    SMALL_CELL = "Small Cell"
    FEMTO = "Femto"


class TowerStatus(str, Enum):
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    OFFLINE = "Offline"
    DECOMMISSIONED = "Decommissioned"


class Tower(Base):
    __tablename__ = "towers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    tower_code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    tower_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    tower_type: Mapped[TowerType] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    coverage_area: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[TowerStatus] = mapped_column(
        String(50),
        nullable=False,
        default=TowerStatus.ACTIVE,
        index=True,
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