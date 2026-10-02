from sqlalchemy import select
from sqlalchemy.orm import Session

from models.sim_replacement_history import (
    SIMReplacementHistory,
)


class SIMReplacementHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        old_sim_id: int,
        new_sim_id: int,
        customer_id: int,
        reason: str | None,
        replaced_by: int,
    ) -> SIMReplacementHistory:

        history = SIMReplacementHistory(
            old_sim_id=old_sim_id,
            new_sim_id=new_sim_id,
            customer_id=customer_id,
            reason=reason,
            replaced_by=replaced_by,
        )

        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)

        return history

    def get_by_sim_id(
        self,
        sim_id: int,
    ) -> list[SIMReplacementHistory]:

        statement = (
            select(SIMReplacementHistory)
            .where(
                (
                    SIMReplacementHistory.old_sim_id
                    == sim_id
                )
                |
                (
                    SIMReplacementHistory.new_sim_id
                    == sim_id
                )
            )
            .order_by(
                SIMReplacementHistory.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )