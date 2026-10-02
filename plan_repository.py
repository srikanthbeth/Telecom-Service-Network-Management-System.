from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.plan import Plan
from utils.enums import PlanStatus, PlanType


class PlanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        plan_id: int,
    ) -> Plan | None:
        return self.db.get(
            Plan,
            plan_id,
        )

    def get_by_name(
        self,
        plan_name: str,
    ) -> Plan | None:
        statement = select(Plan).where(
            Plan.plan_name == plan_name
        )

        return self.db.scalar(statement)

    def create(
        self,
        plan: Plan,
    ) -> Plan:
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)

        return plan

    def update(
        self,
        plan: Plan,
    ) -> Plan:
        self.db.commit()
        self.db.refresh(plan)

        return plan

    def list(
        self,
        search: str | None = None,
        plan_type: PlanType | None = None,
        status: PlanStatus | None = None,
    ) -> List[Plan]:

        statement = select(Plan)

        if search:
            search_value = f"%{search.lower()}%"

            statement = statement.where(
                Plan.plan_name.ilike(search_value)
                |
                Plan.description.ilike(search_value)
            )

        if plan_type:
            statement = statement.where(
                Plan.plan_type == plan_type
            )

        if status:
            statement = statement.where(
                Plan.status == status
            )

        statement = statement.order_by(
            Plan.id.desc()
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_by_ids(
        self,
        plan_ids: List[int],
    ) -> List[Plan]:

        statement = (
            select(Plan)
            .where(Plan.id.in_(plan_ids))
            .order_by(Plan.id)
        )

        return list(
            self.db.scalars(statement).all()
        )