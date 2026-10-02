from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base
from utils.enums import SIMStatus, SIMType


class SIM(Base):
    __tablename__ = "sims"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    sim_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    sim_type: Mapped[SIMType] = mapped_column(
        Enum(SIMType),
        nullable=False,
        index=True,
    )

    status: Mapped[SIMStatus] = mapped_column(
        Enum(SIMStatus),
        nullable=False,
        default=SIMStatus.AVAILABLE,
        index=True,
    )

    activation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"),
        nullable=True,
        index=True,
    )

    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("plans.id"),
        nullable=True,
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

    tower_id: Mapped[int | None] = mapped_column(
    ForeignKey("towers.id"),
    nullable=True,
    index=True,
)