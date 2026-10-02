from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.device_sim_mapping import DeviceSIMMapping


class DeviceSIMMappingRepository:

    def get_active_by_device(
        self,
        db: Session,
        device_id: int,
    ) -> DeviceSIMMapping | None:

        statement = select(DeviceSIMMapping).where(
            DeviceSIMMapping.device_id == device_id,
            DeviceSIMMapping.is_active.is_(True),
        )

        return db.scalar(statement)

    def get_active_by_sim(
        self,
        db: Session,
        sim_id: int,
    ) -> DeviceSIMMapping | None:

        statement = select(DeviceSIMMapping).where(
            DeviceSIMMapping.sim_id == sim_id,
            DeviceSIMMapping.is_active.is_(True),
        )

        return db.scalar(statement)

    def create(
        self,
        db: Session,
        mapping: DeviceSIMMapping,
    ) -> DeviceSIMMapping:

        db.add(mapping)
        db.flush()
        db.refresh(mapping)

        return mapping

    def deactivate(
        self,
        db: Session,
        mapping: DeviceSIMMapping,
    ) -> DeviceSIMMapping:

        mapping.is_active = False
        mapping.unassigned_at = datetime.now(timezone.utc)

        db.flush()
        db.refresh(mapping)

        return mapping

    def get_history_by_device(
        self,
        db: Session,
        device_id: int,
    ):

        statement = (
            select(DeviceSIMMapping)
            .where(
                DeviceSIMMapping.device_id == device_id
            )
            .order_by(
                DeviceSIMMapping.id.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )