from sqlalchemy import select
from sqlalchemy.orm import Session

from models.network_outage import NetworkOutage
from models.outage_customer import OutageCustomer
from models.outage_tower import OutageTower


class NetworkOutageRepository:

    def create(
        self,
        db: Session,
        outage: NetworkOutage,
    ) -> NetworkOutage:

        db.add(outage)
        db.flush()

        return outage

    def get_by_id(
        self,
        db: Session,
        outage_id: int,
    ) -> NetworkOutage | None:

        return db.get(
            NetworkOutage,
            outage_id,
        )

    def get_by_code(
        self,
        db: Session,
        outage_code: str,
    ) -> NetworkOutage | None:

        statement = select(
            NetworkOutage
        ).where(
            NetworkOutage.outage_code == outage_code
        )

        return db.execute(
            statement
        ).scalar_one_or_none()

    def get_all(
        self,
        db: Session,
        severity=None,
        outage_type=None,
    ) -> list[NetworkOutage]:

        statement = select(NetworkOutage)

        if severity:
            statement = statement.where(
                NetworkOutage.severity == severity
            )

        if outage_type:
            statement = statement.where(
                NetworkOutage.outage_type.ilike(
                    f"%{outage_type}%"
                )
            )

        statement = statement.order_by(
            NetworkOutage.start_time.desc()
        )

        return list(
            db.execute(statement).scalars().all()
        )

    def update(
        self,
        db: Session,
        outage: NetworkOutage,
        values: dict,
    ) -> NetworkOutage:

        for key, value in values.items():
            setattr(
                outage,
                key,
                value,
            )

        db.flush()

        return outage

    def delete(
        self,
        db: Session,
        outage: NetworkOutage,
    ) -> None:

        db.delete(outage)
        db.flush()

    def add_tower(
        self,
        db: Session,
        outage_id: int,
        tower_id: int,
    ) -> OutageTower:

        mapping = OutageTower(
            outage_id=outage_id,
            tower_id=tower_id,
        )

        db.add(mapping)
        db.flush()

        return mapping

    def get_tower_ids(
        self,
        db: Session,
        outage_id: int,
    ) -> list[int]:

        statement = select(
            OutageTower.tower_id
        ).where(
            OutageTower.outage_id == outage_id
        )

        return list(
            db.execute(
                statement
            ).scalars().all()
        )

    def add_customer(
        self,
        db: Session,
        outage_id: int,
        customer_id: int,
    ) -> OutageCustomer:

        mapping = OutageCustomer(
            outage_id=outage_id,
            customer_id=customer_id,
        )

        db.add(mapping)
        db.flush()

        return mapping

    def get_customer_ids(
        self,
        db: Session,
        outage_id: int,
    ) -> list[int]:

        statement = select(
            OutageCustomer.customer_id
        ).where(
            OutageCustomer.outage_id == outage_id
        )

        return list(
            db.execute(
                statement
            ).scalars().all()
        )

    def delete_customer_mappings(
        self,
        db: Session,
        outage_id: int,
    ) -> None:

        statement = select(
            OutageCustomer
        ).where(
            OutageCustomer.outage_id == outage_id
        )

        mappings = db.execute(
            statement
        ).scalars().all()

        for mapping in mappings:
            db.delete(mapping)

        db.flush()

    def get_tower_mappings(
        self,
        db: Session,
        outage_id: int,
    ) -> list[OutageTower]:

        statement = select(
            OutageTower
        ).where(
            OutageTower.outage_id == outage_id
        )

        return list(
            db.execute(
                statement
            ).scalars().all()
        )