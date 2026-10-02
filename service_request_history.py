from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base

from utils.enums import ServiceRequestStatus


class ServiceRequestHistory(Base):
    __tablename__ = "service_request_history"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    service_request_id: Mapped[int] = mapped_column(
        ForeignKey("service_requests.id"),
        nullable=False,
        index=True,
    )

    old_status: Mapped[ServiceRequestStatus | None] = mapped_column(
        Enum(ServiceRequestStatus),
        nullable=True,
    )

    new_status: Mapped[ServiceRequestStatus] = mapped_column(
        Enum(ServiceRequestStatus),
        nullable=False,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    changed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )