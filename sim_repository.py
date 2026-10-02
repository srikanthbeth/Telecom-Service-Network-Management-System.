from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.sim import SIM
from utils.enums import SIMStatus, SIMType


class SIMRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        sim_id: int,
    ) -> SIM | None:
        return self.db.get(
            SIM,
            sim_id,
        )

    def get_by_number(
        self,
        sim_number: str,
    ) -> SIM | None:
        statement = select(SIM).where(
            SIM.sim_number == sim_number
        )

        return self.db.scalar(statement)

    def create(
        self,
        sim: SIM,
    ) -> SIM:
        self.db.add(sim)
        self.db.commit()
        self.db.refresh(sim)

        return sim

    def update(
        self,
        sim: SIM,
    ) -> SIM:
        self.db.commit()
        self.db.refresh(sim)

        return sim

    def list(
        self,
        search: str | None = None,
        sim_type: SIMType | None = None,
        status: SIMStatus | None = None,
        customer_id: int | None = None,
        plan_id: int | None = None,
    ) -> List[SIM]:

        statement = select(SIM)

        if search:
            search_value = f"%{search.lower()}%"

            statement = statement.where(
                SIM.sim_number.ilike(
                    search_value
                )
            )

        if sim_type:
            statement = statement.where(
                SIM.sim_type == sim_type
            )

        if status:
            statement = statement.where(
                SIM.status == status
            )

        if customer_id is not None:
            statement = statement.where(
                SIM.customer_id == customer_id
            )

        if plan_id is not None:
            statement = statement.where(
                SIM.plan_id == plan_id
            )

        statement = statement.order_by(
            SIM.id.desc()
        )

        return list(
            self.db.scalars(statement).all()
        )