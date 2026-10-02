from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class OutageCustomer(Base):
    __tablename__ = "outage_customers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    outage_id: Mapped[int] = mapped_column(
        ForeignKey("network_outages.id"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "outage_id",
            "customer_id",
            name="uq_outage_customer",
        ),
    )