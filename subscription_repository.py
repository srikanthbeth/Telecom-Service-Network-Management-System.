from sqlalchemy import select
from sqlalchemy.orm import Session

from models.subscription import Subscription
from utils.enums import SubscriptionStatus


class SubscriptionRepository:

    def get_by_id(
        self,
        db: Session,
        subscription_id: int,
    ) -> Subscription | None:

        return db.get(
            Subscription,
            subscription_id,
        )

    def get_active_by_sim(
        self,
        db: Session,
        sim_id: int,
    ) -> Subscription | None:

        statement = select(Subscription).where(
            Subscription.sim_id == sim_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
        )

        return db.scalar(statement)

    def get_active_by_customer(
        self,
        db: Session,
        customer_id: int,
    ) -> list[Subscription]:

        statement = (
            select(Subscription)
            .where(
                Subscription.customer_id == customer_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
            .order_by(
                Subscription.id.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

    def list(
        self,
        db: Session,
        customer_id: int | None = None,
        sim_id: int | None = None,
        plan_id: int | None = None,
        status: SubscriptionStatus | None = None,
    ) -> list[Subscription]:

        statement = select(Subscription)

        if customer_id is not None:
            statement = statement.where(
                Subscription.customer_id == customer_id
            )

        if sim_id is not None:
            statement = statement.where(
                Subscription.sim_id == sim_id
            )

        if plan_id is not None:
            statement = statement.where(
                Subscription.plan_id == plan_id
            )

        if status is not None:
            statement = statement.where(
                Subscription.status == status
            )

        statement = statement.order_by(
            Subscription.id.desc()
        )

        return list(
            db.scalars(statement).all()
        )

    def create(
        self,
        db: Session,
        subscription: Subscription,
    ) -> Subscription:

        db.add(subscription)
        db.flush()
        db.refresh(subscription)

        return subscription

    def update(
        self,
        db: Session,
        subscription: Subscription,
    ) -> Subscription:

        db.flush()
        db.refresh(subscription)

        return subscription