from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.usage import Usage
from utils.enums import UsageType


class UsageRepository:

    def get_by_id(
        self,
        db: Session,
        usage_id: int,
    ) -> Usage | None:

        return db.get(
            Usage,
            usage_id,
        )

    def create(
        self,
        db: Session,
        usage: Usage,
    ) -> Usage:

        db.add(usage)
        db.flush()
        db.refresh(usage)

        return usage

    def list(
        self,
        db: Session,
        customer_id: int | None = None,
        sim_id: int | None = None,
        subscription_id: int | None = None,
        usage_type: UsageType | None = None,
        usage_date: date | None = None,
    ):

        statement = select(Usage)

        if customer_id is not None:
            statement = statement.where(
                Usage.customer_id == customer_id
            )

        if sim_id is not None:
            statement = statement.where(
                Usage.sim_id == sim_id
            )

        if subscription_id is not None:
            statement = statement.where(
                Usage.subscription_id == subscription_id
            )

        if usage_type is not None:
            statement = statement.where(
                Usage.usage_type == usage_type
            )

        if usage_date is not None:
            statement = statement.where(
                Usage.usage_date == usage_date
            )

        statement = statement.order_by(
            Usage.usage_date.desc(),
            Usage.id.desc(),
        )

        return list(
            db.scalars(statement).all()
        )

    def get_customer_total(
        self,
        db: Session,
        customer_id: int,
        usage_type: UsageType,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> float:

        statement = select(
            func.coalesce(
                func.sum(Usage.quantity),
                0,
            )
        ).where(
            Usage.customer_id == customer_id,
            Usage.usage_type == usage_type,
        )

        if start_date is not None:
            statement = statement.where(
                Usage.usage_date >= start_date
            )

        if end_date is not None:
            statement = statement.where(
                Usage.usage_date <= end_date
            )

        result = db.scalar(statement)

        return float(result or 0)

    def get_sim_total(
        self,
        db: Session,
        sim_id: int,
        usage_type: UsageType,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> float:

        statement = select(
            func.coalesce(
                func.sum(Usage.quantity),
                0,
            )
        ).where(
            Usage.sim_id == sim_id,
            Usage.usage_type == usage_type,
        )

        if start_date is not None:
            statement = statement.where(
                Usage.usage_date >= start_date
            )

        if end_date is not None:
            statement = statement.where(
                Usage.usage_date <= end_date
            )

        result = db.scalar(statement)

        return float(result or 0)

    def count_sim_records(
        self,
        db: Session,
        sim_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> int:

        statement = select(
            func.count(Usage.id)
        ).where(
            Usage.sim_id == sim_id
        )

        if start_date is not None:
            statement = statement.where(
                Usage.usage_date >= start_date
            )

        if end_date is not None:
            statement = statement.where(
                Usage.usage_date <= end_date
            )

        return int(
            db.scalar(statement) or 0
        )