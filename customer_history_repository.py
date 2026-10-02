from sqlalchemy import select
from sqlalchemy.orm import Session

from models.customer_history import CustomerHistory


class CustomerHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        customer_id: int,
        changed_by: int,
        action: str,
        description: str | None = None,
        previous_value: dict | None = None,
        new_value: dict | None = None,
    ) -> CustomerHistory:

        history = CustomerHistory(
            customer_id=customer_id,
            changed_by=changed_by,
            action=action,
            description=description,
            previous_value=previous_value,
            new_value=new_value,
        )

        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)

        return history

    def get_by_customer_id(
        self,
        customer_id: int,
    ) -> list[CustomerHistory]:

        statement = (
            select(CustomerHistory)
            .where(
                CustomerHistory.customer_id
                == customer_id
            )
            .order_by(
                CustomerHistory.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )