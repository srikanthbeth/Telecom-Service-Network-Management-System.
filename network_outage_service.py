from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.network_outage import NetworkOutage
from models.sim import SIM
from models.subscription import Subscription
from models.tower import Tower

from repositories.network_outage_repository import (
    NetworkOutageRepository,
)

from schemas.network_outage import (
    NetworkOutageCreate,
    NetworkOutageResolve,
    NetworkOutageUpdate,
)

from utils.enums import (
    SIMStatus,
    SubscriptionStatus,
)


class NetworkOutageService:

    def __init__(self):
        self.repository = NetworkOutageRepository()

    def create(
        self,
        db: Session,
        data: NetworkOutageCreate,
    ) -> NetworkOutage:

        existing = self.repository.get_by_code(
            db,
            data.outage_code,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Outage code already exists",
            )

        towers = []

        for tower_id in data.tower_ids:
            tower = db.get(Tower, tower_id)

            if not tower:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tower {tower_id} not found",
                )

            towers.append(tower)

        outage = NetworkOutage(
            outage_code=data.outage_code,
            outage_type=data.outage_type,
            description=data.description,
            severity=data.severity,
            start_time=data.start_time,
            expected_resolution=data.expected_resolution,
        )

        self.repository.create(
            db,
            outage,
        )

        for tower in towers:
            self.repository.add_tower(
                db,
                outage.id,
                tower.id,
            )

        customer_ids = self._find_affected_customers(
            db,
            data.tower_ids,
        )

        for customer_id in customer_ids:
            self.repository.add_customer(
                db,
                outage.id,
                customer_id,
            )

        db.commit()
        db.refresh(outage)

        return outage

    def _find_affected_customers(
        self,
        db: Session,
        tower_ids: list[int],
    ) -> list[int]:

        if not tower_ids:
            return []

        statement = (
            select(
                Subscription.customer_id
            )
            .join(
                SIM,
                SIM.id == Subscription.sim_id,
            )
            .where(
                SIM.tower_id.in_(tower_ids),
                SIM.status == SIMStatus.ACTIVE,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.customer_id.is_not(None),
            )
            .distinct()
        )

        return list(
            db.execute(statement)
            .scalars()
            .all()
        )

    def get(
        self,
        db: Session,
        outage_id: int,
    ) -> NetworkOutage:

        outage = self.repository.get_by_id(
            db,
            outage_id,
        )

        if not outage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Network outage not found",
            )

        return outage

    def get_all(
        self,
        db: Session,
        severity=None,
        outage_type=None,
    ):
        return self.repository.get_all(
            db,
            severity=severity,
            outage_type=outage_type,
        )

    def update(
        self,
        db: Session,
        outage_id: int,
        data: NetworkOutageUpdate,
    ) -> NetworkOutage:

        outage = self.get(
            db,
            outage_id,
        )

        values = data.model_dump(
            exclude_unset=True
        )

        self.repository.update(
            db,
            outage,
            values,
        )

        db.commit()
        db.refresh(outage)

        return outage

    def resolve(
        self,
        db: Session,
        outage_id: int,
        data: NetworkOutageResolve,
    ) -> NetworkOutage:

        outage = self.get(
            db,
            outage_id,
        )

        resolution_time = (
            data.actual_resolution
            or datetime.now(timezone.utc)
        )

        if resolution_time < outage.start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Actual resolution cannot be "
                    "before outage start time"
                ),
            )

        outage.actual_resolution = resolution_time

        db.commit()
        db.refresh(outage)

        return outage

    def affected_customers(
        self,
        db: Session,
        outage_id: int,
    ) -> list[int]:

        outage = self.get(
            db,
            outage_id,
        )

        tower_ids = self.repository.get_tower_ids(
            db,
            outage.id,
        )

        if not tower_ids:
            return []

        return self._find_affected_customers(
            db,
            tower_ids,
        )

    def delete(
        self,
        db: Session,
        outage_id: int,
    ):

        outage = self.repository.get_by_id(
            db,
            outage_id,
        )

        if not outage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Network outage not found",
            )

        self.repository.delete_customer_mappings(
            db,
            outage_id,
        )

        tower_mappings = (
            self.repository.get_tower_mappings(
                db,
                outage_id,
            )
        )

        for mapping in tower_mappings:
            db.delete(mapping)

        db.flush()

        db.delete(outage)

        db.commit()