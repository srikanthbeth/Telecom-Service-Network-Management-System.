from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base
from utils.enums import PlanStatus, PlanType


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    plan_name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    plan_type: Mapped[PlanType] = mapped_column(
        Enum(PlanType),
        nullable=False,
        index=True,
    )

    validity_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    data_limit_mb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    voice_limit_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    sms_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus),
        nullable=False,
        default=PlanStatus.ACTIVE,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )