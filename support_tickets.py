from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user,
    require_roles,
)

from db.database import get_db

from schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketResponse,
    SupportTicketUpdate,
    TicketAgentAssignment,
    TicketCommentCreate,
    TicketCommentResponse,
    TicketEscalation,
    TicketHistoryResponse,
    TicketReassignment,
    TicketStatusUpdate,
    TicketTechnicianAssignment,
)

from services.support_ticket_service import (
    SupportTicketService,
)

from utils.enums import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
    UserRole,
)


router = APIRouter(
    prefix="/support-tickets",
    tags=["Support Tickets"],
)

service = SupportTicketService()


# --------------------------------------------------
# CREATE TICKET
# --------------------------------------------------

@router.post(
    "/",
    response_model=SupportTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    data: SupportTicketCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.create(
        db,
        data,
        current_user,
    )


# --------------------------------------------------
# GET ALL TICKETS
# --------------------------------------------------

@router.get(
    "/",
    response_model=list[SupportTicketResponse],
)
def get_tickets(
    customer_id: int | None = Query(
        default=None
    ),
    ticket_status: TicketStatus | None = Query(
        default=None
    ),
    priority: TicketPriority | None = Query(
        default=None
    ),
    category: TicketCategory | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get_all(
        db,
        customer_id=customer_id,
        status_value=ticket_status,
        priority=priority,
        category=category,
    )


# --------------------------------------------------
# GET TICKET
# --------------------------------------------------

@router.get(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get(
        db,
        ticket_id,
    )


# --------------------------------------------------
# UPDATE TICKET
# --------------------------------------------------

@router.put(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
)
def update_ticket(
    ticket_id: int,
    data: SupportTicketUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
        )
    ),
):
    return service.update(
        db,
        ticket_id,
        data,
        current_user,
    )


# --------------------------------------------------
# ASSIGN SUPPORT AGENT
# --------------------------------------------------

@router.patch(
    "/{ticket_id}/assign-agent",
    response_model=SupportTicketResponse,
)
def assign_agent(
    ticket_id: int,
    data: TicketAgentAssignment,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    return service.assign_agent(
        db,
        ticket_id,
        data,
        current_user,
    )


# --------------------------------------------------
# ASSIGN TECHNICIAN
# --------------------------------------------------

@router.patch(
    "/{ticket_id}/assign-technician",
    response_model=SupportTicketResponse,
)
def assign_technician(
    ticket_id: int,
    data: TicketTechnicianAssignment,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
        )
    ),
):
    return service.assign_technician(
        db,
        ticket_id,
        data,
        current_user,
    )


# --------------------------------------------------
# REASSIGN
# --------------------------------------------------

@router.patch(
    "/{ticket_id}/reassign",
    response_model=SupportTicketResponse,
)
def reassign_ticket(
    ticket_id: int,
    data: TicketReassignment,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
        )
    ),
):
    return service.reassign(
        db,
        ticket_id,
        data,
        current_user,
    )


# --------------------------------------------------
# STATUS
# --------------------------------------------------

@router.patch(
    "/{ticket_id}/status",
    response_model=SupportTicketResponse,
)
def update_status(
    ticket_id: int,
    data: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.NETWORK_ENGINEER,
            UserRole.FIELD_TECHNICIAN,
        )
    ),
):
    return service.update_status(
        db,
        ticket_id,
        data,
        current_user,
    )


# --------------------------------------------------
# ESCALATE
# --------------------------------------------------

@router.patch(
    "/{ticket_id}/escalate",
    response_model=SupportTicketResponse,
)
def escalate_ticket(
    ticket_id: int,
    data: TicketEscalation,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
        )
    ),
):
    return service.escalate(
        db,
        ticket_id,
        data,
        current_user,
    )


# --------------------------------------------------
# INTERNAL COMMENTS
# --------------------------------------------------

@router.post(
    "/{ticket_id}/comments",
    response_model=TicketCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    ticket_id: int,
    data: TicketCommentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.NETWORK_ENGINEER,
            UserRole.FIELD_TECHNICIAN,
        )
    ),
):
    return service.add_comment(
        db,
        ticket_id,
        data,
        current_user,
    )


@router.get(
    "/{ticket_id}/comments",
    response_model=list[TicketCommentResponse],
)
def get_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get_comments(
        db,
        ticket_id,
    )


# --------------------------------------------------
# TICKET HISTORY
# --------------------------------------------------

@router.get(
    "/{ticket_id}/history",
    response_model=list[TicketHistoryResponse],
)
def get_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get_history(
        db,
        ticket_id,
    )