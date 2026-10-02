from sqlalchemy import select
from sqlalchemy.orm import Session

from models.subscription_history import SubscriptionHistory


class SubscriptionHistoryRepository:

    def create(
        self,
        db: Session,
        history: SubscriptionHistory,
    ) -> SubscriptionHistory:

        db.add(history)
        db.flush()
        db.refresh(history)

        return history

    def get_by_subscription_id(
        self,
        db: Session,
        subscription_id: int,
    ) -> list[SubscriptionHistory]:

        statement = (
            select(SubscriptionHistory)
            .where(
                SubscriptionHistory.subscription_id
                == subscription_id
            )
            .order_by(
                SubscriptionHistory.id.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )