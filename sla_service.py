from datetime import datetime, timedelta, timezone
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.customer import Customer
from models.sla_rule import SLARule
from models.support_ticket import SupportTicket
from models.ticket_sla import TicketSLA
from models.user import User

from repositories.sla_repository import SLARepository

from schemas.sla import (
    SLARuleCreate,
    SLARuleUpdate,
)

from utils.enums import (
    SLAEscalationStatus,
    SLAStatus,
    TicketStatus,
)


class SLAService:

    def __init__(self):
        self.repository = SLARepository()

    # =========================================================
    # HELPERS
    # =========================================================

    def _value(self, value):
        if hasattr(value, "value"):
            return value.value

        return value

    def _customer_type(
        self,
        customer: Customer,
    ):
        customer_type = getattr(
            customer,
            "customer_type",
            None,
        )

        if hasattr(customer_type, "value"):
            return customer_type.value

        if customer_type:
            return customer_type

        return "Standard"

    def _normalize_datetime(self, value):
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        )

    # =========================================================
    # SLA RULES
    # =========================================================

    def create_rule(
        self,
        db: Session,
        data: SLARuleCreate,
        current_user: User,
    ):
        existing = self.repository.get_rule_by_name(
            db,
            data.rule_name,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="SLA rule with this name already exists",
            )

        rule = SLARule(
            rule_name=data.rule_name,
            ticket_category=data.ticket_category,
            priority=data.priority,
            customer_type=data.customer_type,
            sla_minutes=data.sla_minutes,
            warning_minutes=data.warning_minutes,
            escalation_enabled=data.escalation_enabled,
            is_active=data.is_active,
        )

        self.repository.create_rule(
            db,
            rule,
        )

        db.commit()
        db.refresh(rule)

        return rule

    def get_rule(
        self,
        db: Session,
        rule_id: int,
    ):
        rule = self.repository.get_rule_by_id(
            db,
            rule_id,
        )

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA rule not found",
            )

        return rule

    def get_rules(
        self,
        db: Session,
        is_active: bool | None = None,
    ):
        return self.repository.get_rules(
            db,
            is_active=is_active,
        )

    def update_rule(
        self,
        db: Session,
        rule_id: int,
        data: SLARuleUpdate,
        current_user: User,
    ):
        rule = self.get_rule(
            db,
            rule_id,
        )

        values = data.model_dump(
            exclude_unset=True,
        )

        if "rule_name" in values:
            existing = self.repository.get_rule_by_name(
                db,
                values["rule_name"],
            )

            if existing and existing.id != rule.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="SLA rule with this name already exists",
                )

        self.repository.update_rule(
            db,
            rule,
            values,
        )

        db.commit()
        db.refresh(rule)

        return rule

    # =========================================================
    # FIND MATCHING SLA RULE
    # =========================================================

    def find_matching_rule(
        self,
        db: Session,
        ticket: SupportTicket,
    ):
        customer = db.get(
            Customer,
            ticket.customer_id,
        )

        if not customer:
            return None

        ticket_category = self._value(
            ticket.category
        )

        ticket_priority = self._value(
            ticket.priority
        )

        customer_type = self._customer_type(
            customer
        )

        rules = self.repository.get_rules(
            db,
            is_active=True,
        )

        matches = []

        for rule in rules:

            rule_category = self._value(
                rule.ticket_category
            )

            rule_priority = self._value(
                rule.priority
            )

            rule_customer_type = self._value(
                rule.customer_type
            )

            # -------------------------------------------------
            # Category must match if specified
            # -------------------------------------------------

            if (
                rule_category is not None
                and rule_category != ticket_category
            ):
                continue

            # -------------------------------------------------
            # Priority must match if specified
            # -------------------------------------------------

            if (
                rule_priority is not None
                and rule_priority != ticket_priority
            ):
                continue

            # -------------------------------------------------
            # Customer type must match if specified
            # -------------------------------------------------

            if (
                rule_customer_type is not None
                and rule_customer_type != customer_type
            ):
                continue

            # -------------------------------------------------
            # Calculate specificity
            # -------------------------------------------------

            specificity = 0

            if rule_category is not None:
                specificity += 1

            if rule_priority is not None:
                specificity += 1

            if rule_customer_type is not None:
                specificity += 1

            # -------------------------------------------------
            # Normalize created_at
            # -------------------------------------------------

            created_at = rule.created_at

            if created_at is None:
                created_at = datetime.min.replace(
                    tzinfo=timezone.utc
                )

            elif created_at.tzinfo is None:
                created_at = created_at.replace(
                    tzinfo=timezone.utc
                )

            else:
                created_at = created_at.astimezone(
                    timezone.utc
                )

            matches.append(
                (
                    created_at,
                    specificity,
                    rule.id,
                    rule,
                )
            )

        if not matches:
            return None

        # -----------------------------------------------------
        # Rule selection priority
        #
        # 1. Newest matching rule
        # 2. More specific matching rule
        # 3. Higher rule ID
        #
        # This prevents an old SLA rule from overriding a
        # newly-created rule simply because the old rule has
        # one additional matching condition.
        # -----------------------------------------------------

        matches.sort(
            key=lambda item: (
                item[0],
                item[1],
                item[2],
            ),
            reverse=True,
        )

        return matches[0][3]

    # =========================================================
    # START SLA
    # =========================================================

    def start_ticket_sla(
        self,
        db: Session,
        ticket_id: int,
        current_user: User | None = None,
    ):
        ticket = db.get(
            SupportTicket,
            ticket_id,
        )

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        # -----------------------------------------------------
        # Always determine the correct matching rule first.
        # -----------------------------------------------------

        rule = self.find_matching_rule(
            db,
            ticket,
        )

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No matching SLA rule found",
            )

        # -----------------------------------------------------
        # Check whether SLA already exists.
        # -----------------------------------------------------

        existing = self.repository.get_ticket_sla(
            db,
            ticket_id,
        )

        if existing:

            # -------------------------------------------------
            # If existing SLA already uses the correct rule,
            # return it.
            # -------------------------------------------------

            if existing.sla_rule_id == rule.id:
                return existing

            # -------------------------------------------------
            # If an old/wrong SLA exists, update it to the
            # correct matching rule.
            # -------------------------------------------------

            existing.sla_rule_id = rule.id

            start_time = self._normalize_datetime(
                existing.start_time
            )

            if start_time is None:
                start_time = datetime.now(
                    timezone.utc
                )

                existing.start_time = start_time

            existing.deadline = (
                start_time
                + timedelta(
                    minutes=rule.sla_minutes
                )
            )

            existing.status = (
                SLAStatus.ACTIVE.value
            )

            existing.is_breached = False

            existing.escalation_status = (
                SLAEscalationStatus.NOT_ESCALATED.value
            )

            existing.escalated_at = None
            existing.resolution_time = None
            existing.resolution_minutes = None

            db.commit()
            db.refresh(existing)

            return existing

        # -----------------------------------------------------
        # Create new SLA
        # -----------------------------------------------------

        start_time = datetime.now(
            timezone.utc
        )

        deadline = (
            start_time
            + timedelta(
                minutes=rule.sla_minutes
            )
        )

        ticket_sla = TicketSLA(
            ticket_id=ticket.id,
            sla_rule_id=rule.id,
            start_time=start_time,
            deadline=deadline,
            status=SLAStatus.ACTIVE.value,
            is_breached=False,
            escalation_status=(
                SLAEscalationStatus.NOT_ESCALATED.value
            ),
        )

        self.repository.create_ticket_sla(
            db,
            ticket_sla,
        )

        db.commit()
        db.refresh(ticket_sla)

        return ticket_sla

    # =========================================================
    # REFRESH SLA STATUS
    # =========================================================

    def _refresh_sla_status(
        self,
        db: Session,
        ticket_sla: TicketSLA,
    ):
        now = datetime.now(
            timezone.utc
        )

        ticket = db.get(
            SupportTicket,
            ticket_sla.ticket_id,
        )

        if not ticket:
            return ticket_sla

        ticket_status = self._value(
            ticket.status
        )

        # -----------------------------------------------------
        # Resolved / Closed
        # -----------------------------------------------------

        if ticket_status in (
            self._value(TicketStatus.RESOLVED),
            self._value(TicketStatus.CLOSED),
        ):

            if ticket_sla.resolution_time is None:

                resolution_time = (
                    ticket.resolved_at
                    or ticket.closed_at
                    or now
                )

                resolution_time = (
                    self._normalize_datetime(
                        resolution_time
                    )
                )

                start_time = (
                    self._normalize_datetime(
                        ticket_sla.start_time
                    )
                )

                ticket_sla.resolution_time = (
                    resolution_time
                )

                elapsed = (
                    resolution_time
                    - start_time
                )

                ticket_sla.resolution_minutes = max(
                    0,
                    int(
                        elapsed.total_seconds()
                        // 60
                    ),
                )

            ticket_sla.status = (
                SLAStatus.RESOLVED.value
            )

            return ticket_sla

        # -----------------------------------------------------
        # Deadline breach
        # -----------------------------------------------------

        deadline = self._normalize_datetime(
            ticket_sla.deadline
        )

        if now >= deadline:

            ticket_sla.status = (
                SLAStatus.BREACHED.value
            )

            ticket_sla.is_breached = True

            ticket_sla.escalation_status = (
                SLAEscalationStatus.ESCALATED.value
            )

            if ticket_sla.escalated_at is None:
                ticket_sla.escalated_at = now

            return ticket_sla

        # -----------------------------------------------------
        # Warning status
        # -----------------------------------------------------

        rule = db.get(
            SLARule,
            ticket_sla.sla_rule_id,
        )

        if rule:

            warning_start = (
                deadline
                - timedelta(
                    minutes=rule.warning_minutes
                )
            )

            if now >= warning_start:
                ticket_sla.escalation_status = (
                    SLAEscalationStatus.WARNING.value
                )

        return ticket_sla

    # =========================================================
    # GET TICKET SLA
    # =========================================================

    def get_ticket_sla(
        self,
        db: Session,
        ticket_id: int,
    ):
        ticket_sla = self.repository.get_ticket_sla(
            db,
            ticket_id,
        )

        if not ticket_sla:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA tracking record not found",
            )

        self._refresh_sla_status(
            db,
            ticket_sla,
        )

        db.commit()
        db.refresh(ticket_sla)

        return ticket_sla

    # =========================================================
    # RESOLVE SLA
    # =========================================================

    def resolve_ticket_sla(
        self,
        db: Session,
        ticket_id: int,
        current_user: User,
    ):
        ticket_sla = self.repository.get_ticket_sla(
            db,
            ticket_id,
        )

        if not ticket_sla:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA tracking record not found",
            )

        ticket = db.get(
            SupportTicket,
            ticket_id,
        )

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        resolution_time = (
            ticket.resolved_at
            or ticket.closed_at
            or datetime.now(timezone.utc)
        )

        resolution_time = self._normalize_datetime(
            resolution_time
        )

        start_time = self._normalize_datetime(
            ticket_sla.start_time
        )

        deadline = self._normalize_datetime(
            ticket_sla.deadline
        )

        ticket_sla.resolution_time = (
            resolution_time
        )

        elapsed = (
            resolution_time
            - start_time
        )

        ticket_sla.resolution_minutes = max(
            0,
            int(
                elapsed.total_seconds()
                // 60
            ),
        )

        ticket_sla.status = (
            SLAStatus.RESOLVED.value
        )

        if resolution_time > deadline:

            ticket_sla.is_breached = True

            ticket_sla.escalation_status = (
                SLAEscalationStatus.ESCALATED.value
            )

            if ticket_sla.escalated_at is None:
                ticket_sla.escalated_at = (
                    resolution_time
                )

        else:
            ticket_sla.is_breached = False

        db.commit()
        db.refresh(ticket_sla)

        return ticket_sla

    # =========================================================
    # BREACHED TICKETS
    # =========================================================

    def get_breached_tickets(
        self,
        db: Session,
    ):
        now = datetime.now(
            timezone.utc
        )

        statement = (
            select(
                TicketSLA,
                SupportTicket,
            )
            .join(
                SupportTicket,
                SupportTicket.id
                == TicketSLA.ticket_id,
            )
            .where(
                TicketSLA.deadline < now,
                TicketSLA.status
                == SLAStatus.ACTIVE.value,
                SupportTicket.status.notin_(
                    [
                        TicketStatus.RESOLVED,
                        TicketStatus.CLOSED,
                    ]
                ),
            )
            .order_by(
                TicketSLA.deadline.asc()
            )
        )

        rows = db.execute(
            statement
        ).all()

        results = []

        for ticket_sla, ticket in rows:

            self._refresh_sla_status(
                db,
                ticket_sla,
            )

            results.append(
                ticket_sla
            )

        db.commit()

        return results

    # =========================================================
    # SOON TO BREACH
    # =========================================================

    def get_soon_to_breach_tickets(
        self,
        db: Session,
        minutes: int = 60,
    ):
        if minutes <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minutes must be greater than zero",
            )

        now = datetime.now(
            timezone.utc
        )

        deadline_limit = (
            now
            + timedelta(
                minutes=minutes
            )
        )

        statement = (
            select(
                TicketSLA,
                SupportTicket,
            )
            .join(
                SupportTicket,
                SupportTicket.id
                == TicketSLA.ticket_id,
            )
            .where(
                TicketSLA.deadline > now,
                TicketSLA.deadline <= deadline_limit,
                TicketSLA.status
                == SLAStatus.ACTIVE.value,
                SupportTicket.status.notin_(
                    [
                        TicketStatus.RESOLVED,
                        TicketStatus.CLOSED,
                    ]
                ),
            )
            .order_by(
                TicketSLA.deadline.asc()
            )
        )

        rows = db.execute(
            statement
        ).all()

        results = []

        for ticket_sla, ticket in rows:

            self._refresh_sla_status(
                db,
                ticket_sla,
            )

            results.append(
                ticket_sla
            )

        db.commit()

        return results

    # =========================================================
    # SLA STATUS
    # =========================================================

    def get_sla_status(
        self,
        db: Session,
        ticket_id: int,
    ):
        ticket = db.get(
            SupportTicket,
            ticket_id,
        )

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        ticket_sla = self.repository.get_ticket_sla(
            db,
            ticket_id,
        )

        if not ticket_sla:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA tracking record not found",
            )

        self._refresh_sla_status(
            db,
            ticket_sla,
        )

        now = datetime.now(
            timezone.utc
        )

        deadline = self._normalize_datetime(
            ticket_sla.deadline
        )

        if ticket_sla.status == SLAStatus.ACTIVE.value:

            seconds = (
                deadline - now
            ).total_seconds()

            minutes_remaining = max(
                0,
                int(
                    ceil(
                        seconds / 60
                    )
                ),
            )

        else:
            minutes_remaining = None

        db.commit()

        return {
            "ticket_id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "status": (
                ticket.status.value
                if hasattr(ticket.status, "value")
                else ticket.status
            ),
            "sla_status": ticket_sla.status,
            "start_time": ticket_sla.start_time,
            "deadline": ticket_sla.deadline,
            "resolution_time": (
                ticket_sla.resolution_time
            ),
            "resolution_minutes": (
                ticket_sla.resolution_minutes
            ),
            "is_breached": (
                ticket_sla.is_breached
            ),
            "escalation_status": (
                ticket_sla.escalation_status
            ),
            "minutes_remaining": (
                minutes_remaining
            ),
        }