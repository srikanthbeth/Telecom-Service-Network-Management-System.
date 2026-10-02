from sqlalchemy import select
from sqlalchemy.orm import Session

from models.support_ticket import SupportTicket
from models.ticket_comment import TicketComment
from models.ticket_history import TicketHistory


class SupportTicketRepository:

    def create(
        self,
        db: Session,
        ticket: SupportTicket,
    ):
        db.add(ticket)
        db.flush()
        return ticket

    def get_by_id(
        self,
        db: Session,
        ticket_id: int,
    ):
        return db.get(
            SupportTicket,
            ticket_id,
        )

    def get_by_number(
        self,
        db: Session,
        ticket_number: str,
    ):
        statement = select(
            SupportTicket
        ).where(
            SupportTicket.ticket_number
            == ticket_number
        )

        return db.execute(
            statement
        ).scalar_one_or_none()

    def get_all(
        self,
        db: Session,
        customer_id=None,
        status=None,
        priority=None,
        category=None,
    ):
        statement = select(SupportTicket)

        if customer_id is not None:
            statement = statement.where(
                SupportTicket.customer_id
                == customer_id
            )

        if status is not None:
            statement = statement.where(
                SupportTicket.status
                == status
            )

        if priority is not None:
            statement = statement.where(
                SupportTicket.priority
                == priority
            )

        if category is not None:
            statement = statement.where(
                SupportTicket.category
                == category
            )

        statement = statement.order_by(
            SupportTicket.created_at.desc()
        )

        return list(
            db.execute(statement)
            .scalars()
            .all()
        )

    def update(
        self,
        db: Session,
        ticket: SupportTicket,
        values: dict,
    ):
        for key, value in values.items():
            setattr(
                ticket,
                key,
                value,
            )

        db.flush()

        return ticket

    def add_comment(
        self,
        db: Session,
        comment: TicketComment,
    ):
        db.add(comment)
        db.flush()
        return comment

    def get_comments(
        self,
        db: Session,
        ticket_id: int,
    ):
        statement = (
            select(TicketComment)
            .where(
                TicketComment.ticket_id
                == ticket_id
            )
            .order_by(
                TicketComment.created_at.asc()
            )
        )

        return list(
            db.execute(statement)
            .scalars()
            .all()
        )

    def add_history(
        self,
        db: Session,
        history: TicketHistory,
    ):
        db.add(history)
        db.flush()
        return history

    def get_history(
        self,
        db: Session,
        ticket_id: int,
    ):
        statement = (
            select(TicketHistory)
            .where(
                TicketHistory.ticket_id
                == ticket_id
            )
            .order_by(
                TicketHistory.created_at.asc()
            )
        )

        return list(
            db.execute(statement)
            .scalars()
            .all()
        )