from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.customer import Customer
from models.technician import Technician
from models.support_ticket import SupportTicket
from models.ticket_comment import TicketComment
from models.ticket_history import TicketHistory
from models.user import User

from repositories.support_ticket_repository import (
    SupportTicketRepository,
)

from schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketUpdate,
    TicketAgentAssignment,
    TicketCommentCreate,
    TicketEscalation,
    TicketReassignment,
    TicketStatusUpdate,
    TicketTechnicianAssignment,
)

from services.sla_service import SLAService

from utils.enums import (
    TicketHistoryAction,
    TicketStatus,
    UserRole,
)


class SupportTicketService:

    def __init__(self):
        self.repository = SupportTicketRepository()
        self.sla_service = SLAService()

    def _generate_ticket_number(self):
        return f"TKT-{uuid4().hex[:10].upper()}"

    def _add_history(
        self,
        db: Session,
        ticket_id: int,
        action,
        changed_by: int | None,
        old_value=None,
        new_value=None,
        description=None,
    ):
        history = TicketHistory(
            ticket_id=ticket_id,
            action=(
                action.value
                if hasattr(action, "value")
                else action
            ),
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            description=description,
        )

        self.repository.add_history(
            db,
            history,
        )

    # =========================================================
    # CREATE TICKET
    # =========================================================

    def create(
        self,
        db: Session,
        data: SupportTicketCreate,
        current_user: User,
    ):
        customer = db.get(
            Customer,
            data.customer_id,
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        ticket = SupportTicket(
            ticket_number=self._generate_ticket_number(),
            customer_id=data.customer_id,
            category=data.category,
            subject=data.subject,
            description=data.description,
            priority=data.priority,
            status=TicketStatus.OPEN,
        )

        self.repository.create(
            db,
            ticket,
        )

        # -----------------------------------------------------
        # CREATE TICKET HISTORY
        # -----------------------------------------------------

        self._add_history(
            db,
            ticket.id,
            TicketHistoryAction.CREATED,
            current_user.id,
            new_value=TicketStatus.OPEN.value,
            description="Support ticket created",
        )

        # -----------------------------------------------------
        # AUTOMATICALLY START SLA
        #
        # If a matching SLA rule exists, create TicketSLA.
        #
        # If no SLA rule exists, ticket creation should still
        # succeed. This keeps the existing Level 13 behavior.
        # -----------------------------------------------------

        matching_rule = self.sla_service.find_matching_rule(
            db,
            ticket,
        )

        if matching_rule:
            self.sla_service.start_ticket_sla(
                db,
                ticket.id,
                current_user,
            )

        db.commit()
        db.refresh(ticket)

        return ticket

    # =========================================================
    # GET TICKET
    # =========================================================

    def get(
        self,
        db: Session,
        ticket_id: int,
    ):
        ticket = self.repository.get_by_id(
            db,
            ticket_id,
        )

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        return ticket

    # =========================================================
    # GET ALL
    # =========================================================

    def get_all(
        self,
        db: Session,
        customer_id=None,
        status_value=None,
        priority=None,
        category=None,
    ):
        return self.repository.get_all(
            db,
            customer_id=customer_id,
            status=status_value,
            priority=priority,
            category=category,
        )

    # =========================================================
    # UPDATE TICKET
    # =========================================================

    def update(
        self,
        db: Session,
        ticket_id: int,
        data: SupportTicketUpdate,
        current_user: User,
    ):
        ticket = self.get(
            db,
            ticket_id,
        )

        values = data.model_dump(
            exclude_unset=True,
        )

        if "priority" in values:

            old_priority = (
                ticket.priority.value
                if hasattr(ticket.priority, "value")
                else ticket.priority
            )

            new_priority = values["priority"]

            new_priority_value = (
                new_priority.value
                if hasattr(new_priority, "value")
                else new_priority
            )

            if old_priority != new_priority_value:

                self._add_history(
                    db,
                    ticket.id,
                    TicketHistoryAction.PRIORITY_CHANGED,
                    current_user.id,
                    old_value=old_priority,
                    new_value=new_priority_value,
                )

        self.repository.update(
            db,
            ticket,
            values,
        )

        db.commit()
        db.refresh(ticket)

        return ticket

    # =========================================================
    # ASSIGN SUPPORT AGENT
    # =========================================================

    def assign_agent(
        self,
        db: Session,
        ticket_id: int,
        data: TicketAgentAssignment,
        current_user: User,
    ):
        ticket = self.get(
            db,
            ticket_id,
        )

        agent = db.get(
            User,
            data.agent_id,
        )

        if not agent:
            raise HTTPException(
                status_code=404,
                detail="Support agent not found",
            )

        if agent.role != UserRole.SUPPORT_AGENT:
            raise HTTPException(
                status_code=400,
                detail="Selected user is not a Support Agent",
            )

        old_agent = ticket.assigned_agent_id

        ticket.assigned_agent_id = data.agent_id

        if ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.ASSIGNED

        self._add_history(
            db,
            ticket.id,
            (
                TicketHistoryAction.ASSIGNED
                if old_agent is None
                else TicketHistoryAction.REASSIGNED
            ),
            current_user.id,
            old_value=(
                str(old_agent)
                if old_agent
                else None
            ),
            new_value=str(data.agent_id),
            description="Support agent assigned",
        )

        db.commit()
        db.refresh(ticket)

        return ticket

    # =========================================================
    # ASSIGN TECHNICIAN
    # =========================================================

    def assign_technician(
        self,
        db: Session,
        ticket_id: int,
        data: TicketTechnicianAssignment,
        current_user: User,
    ):
        ticket = self.get(
            db,
            ticket_id,
        )

        technician = db.get(
            Technician,
            data.technician_id,
        )

        if not technician:
            raise HTTPException(
                status_code=404,
                detail="Technician not found",
            )

        availability = (
            technician.availability.value
            if hasattr(
                technician.availability,
                "value",
            )
            else technician.availability
        )

        if availability in [
            "On Leave",
            "Unavailable",
        ]:
            raise HTTPException(
                status_code=400,
                detail="Technician is not available",
            )

        old_technician = (
            ticket.assigned_technician_id
        )

        ticket.assigned_technician_id = (
            data.technician_id
        )

        if ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.ASSIGNED

        self._add_history(
            db,
            ticket.id,
            (
                TicketHistoryAction.ASSIGNED
                if old_technician is None
                else TicketHistoryAction.REASSIGNED
            ),
            current_user.id,
            old_value=(
                str(old_technician)
                if old_technician
                else None
            ),
            new_value=str(
                data.technician_id
            ),
            description="Field technician assigned",
        )

        db.commit()
        db.refresh(ticket)

        return ticket

    # =========================================================
    # REASSIGN
    # =========================================================

    def reassign(
        self,
        db: Session,
        ticket_id: int,
        data: TicketReassignment,
        current_user: User,
    ):

        if (
            data.agent_id is None
            and data.technician_id is None
        ):
            raise HTTPException(
                status_code=400,
                detail="Agent ID or technician ID is required",
            )

        if (
            data.agent_id is not None
            and data.technician_id is not None
        ):
            raise HTTPException(
                status_code=400,
                detail="Assign either an agent or technician",
            )

        ticket = self.get(
            db,
            ticket_id,
        )

        old_agent = ticket.assigned_agent_id

        old_technician = (
            ticket.assigned_technician_id
        )

        if data.agent_id is not None:

            agent = db.get(
                User,
                data.agent_id,
            )

            if not agent:
                raise HTTPException(
                    status_code=404,
                    detail="Support agent not found",
                )

            if agent.role != UserRole.SUPPORT_AGENT:
                raise HTTPException(
                    status_code=400,
                    detail="Selected user is not a Support Agent",
                )

            ticket.assigned_agent_id = (
                data.agent_id
            )

            ticket.assigned_technician_id = None

            new_value = str(
                data.agent_id
            )

        else:

            technician = db.get(
                Technician,
                data.technician_id,
            )

            if not technician:
                raise HTTPException(
                    status_code=404,
                    detail="Technician not found",
                )

            availability = (
                technician.availability.value
                if hasattr(
                    technician.availability,
                    "value",
                )
                else technician.availability
            )

            if availability in [
                "On Leave",
                "Unavailable",
            ]:
                raise HTTPException(
                    status_code=400,
                    detail="Technician is not available",
                )

            ticket.assigned_technician_id = (
                data.technician_id
            )

            ticket.assigned_agent_id = None

            new_value = str(
                data.technician_id
            )

        self._add_history(
            db,
            ticket.id,
            TicketHistoryAction.REASSIGNED,
            current_user.id,
            old_value=(
                str(old_agent)
                if old_agent
                else (
                    str(old_technician)
                    if old_technician
                    else None
                )
            ),
            new_value=new_value,
            description="Ticket reassigned",
        )

        if ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.ASSIGNED

        db.commit()
        db.refresh(ticket)

        return ticket

    # =========================================================
    # UPDATE STATUS
    # =========================================================

    def update_status(
        self,
        db: Session,
        ticket_id: int,
        data: TicketStatusUpdate,
        current_user: User,
    ):
        ticket = self.get(
            db,
            ticket_id,
        )

        old_status = ticket.status

        if old_status == data.status:
            return ticket

        ticket.status = data.status

        now = datetime.now(timezone.utc)

        # -----------------------------------------------------
        # RESOLVED
        # -----------------------------------------------------

        if data.status == TicketStatus.RESOLVED:

            ticket.resolved_at = now

            if data.resolution_notes:
                ticket.resolution_notes = (
                    data.resolution_notes
                )

            self._add_history(
                db,
                ticket.id,
                TicketHistoryAction.RESOLUTION_ADDED,
                current_user.id,
                new_value=data.resolution_notes,
                description="Ticket resolution added",
            )

        # -----------------------------------------------------
        # CLOSED
        # -----------------------------------------------------

        if data.status == TicketStatus.CLOSED:

            ticket.closed_at = now

            self._add_history(
                db,
                ticket.id,
                TicketHistoryAction.CLOSED,
                current_user.id,
                old_value=(
                    old_status.value
                    if hasattr(old_status, "value")
                    else old_status
                ),
                new_value=(
                    data.status.value
                    if hasattr(data.status, "value")
                    else data.status
                ),
            )

        self._add_history(
            db,
            ticket.id,
            TicketHistoryAction.STATUS_CHANGED,
            current_user.id,
            old_value=(
                old_status.value
                if hasattr(old_status, "value")
                else old_status
            ),
            new_value=(
                data.status.value
                if hasattr(data.status, "value")
                else data.status
            ),
        )

        db.commit()
        db.refresh(ticket)

        return ticket

    # =========================================================
    # ESCALATE
    # =========================================================

    def escalate(
        self,
        db: Session,
        ticket_id: int,
        data: TicketEscalation,
        current_user: User,
    ):
        ticket = self.get(
            db,
            ticket_id,
        )

        old_level = ticket.escalation_level

        ticket.escalation_level = (
            data.escalation_level
        )

        ticket.is_escalated = True

        self._add_history(
            db,
            ticket.id,
            TicketHistoryAction.ESCALATED,
            current_user.id,
            old_value=str(old_level),
            new_value=str(
                data.escalation_level
            ),
            description=data.reason,
        )

        db.commit()
        db.refresh(ticket)

        return ticket

    # =========================================================
    # COMMENTS
    # =========================================================

    def add_comment(
        self,
        db: Session,
        ticket_id: int,
        data: TicketCommentCreate,
        current_user: User,
    ):
        self.get(
            db,
            ticket_id,
        )

        comment = TicketComment(
            ticket_id=ticket_id,
            author_id=current_user.id,
            comment=data.comment,
        )

        self.repository.add_comment(
            db,
            comment,
        )

        self._add_history(
            db,
            ticket_id,
            TicketHistoryAction.COMMENT_ADDED,
            current_user.id,
            description="Internal comment added",
        )

        db.commit()
        db.refresh(comment)

        return comment

    def get_comments(
        self,
        db: Session,
        ticket_id: int,
    ):
        self.get(
            db,
            ticket_id,
        )

        return self.repository.get_comments(
            db,
            ticket_id,
        )

    def get_history(
        self,
        db: Session,
        ticket_id: int,
    ):
        self.get(
            db,
            ticket_id,
        )

        return self.repository.get_history(
            db,
            ticket_id,
        )