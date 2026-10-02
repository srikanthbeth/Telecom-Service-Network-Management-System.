from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class OutageTower(Base):
    __tablename__ = "outage_towers"

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

    tower_id: Mapped[int] = mapped_column(
        ForeignKey("towers.id"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "outage_id",
            "tower_id",
            name="uq_outage_tower",
        ),
    )