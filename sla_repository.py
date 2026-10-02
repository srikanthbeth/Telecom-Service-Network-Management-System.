from sqlalchemy import select
from sqlalchemy.orm import Session

from models.sla_rule import SLARule
from models.ticket_sla import TicketSLA


class SLARepository:

    def create_rule(
        self,
        db: Session,
        rule: SLARule,
    ):
        db.add(rule)
        db.flush()

        return rule

    def get_rule_by_id(
        self,
        db: Session,
        rule_id: int,
    ):
        return db.get(
            SLARule,
            rule_id,
        )

    def get_rule_by_name(
        self,
        db: Session,
        rule_name: str,
    ):
        statement = select(SLARule).where(
            SLARule.rule_name == rule_name
        )

        return db.execute(
            statement
        ).scalar_one_or_none()

    def get_rules(
        self,
        db: Session,
        is_active: bool | None = None,
    ):
        statement = select(SLARule)

        if is_active is not None:
            statement = statement.where(
                SLARule.is_active == is_active
            )

        statement = statement.order_by(
            SLARule.created_at.desc()
        )

        return list(
            db.execute(statement)
            .scalars()
            .all()
        )

    def update_rule(
        self,
        db: Session,
        rule: SLARule,
        values: dict,
    ):
        for key, value in values.items():
            setattr(
                rule,
                key,
                value,
            )

        db.flush()

        return rule

    def create_ticket_sla(
        self,
        db: Session,
        ticket_sla: TicketSLA,
    ):
        db.add(ticket_sla)
        db.flush()

        return ticket_sla

    def get_ticket_sla(
        self,
        db: Session,
        ticket_id: int,
    ):
        statement = select(TicketSLA).where(
            TicketSLA.ticket_id == ticket_id
        )

        return db.execute(
            statement
        ).scalar_one_or_none()

    def get_all_ticket_slas(
        self,
        db: Session,
    ):
        statement = select(TicketSLA).order_by(
            TicketSLA.deadline.asc()
        )

        return list(
            db.execute(statement)
            .scalars()
            .all()
        )

    def get_active_ticket_slas(
        self,
        db: Session,
    ):
        statement = select(TicketSLA).where(
            TicketSLA.status == "Active"
        )

        return list(
            db.execute(statement)
            .scalars()
            .all()
        )