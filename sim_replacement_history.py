from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class SIMReplacementHistory(Base):
    __tablename__ = "sim_replacement_history"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    old_sim_id: Mapped[int] = mapped_column(
        ForeignKey("sims.id"),
        nullable=False,
        index=True,
    )

    new_sim_id: Mapped[int] = mapped_column(
        ForeignKey("sims.id"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    replaced_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )