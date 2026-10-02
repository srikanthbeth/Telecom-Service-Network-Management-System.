from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user,
    require_roles,
)

from db.database import get_db

from schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestHistoryResponse,
    ServiceRequestResponse,
    ServiceRequestStatusUpdate,
)

from services.service_request_service import (
    ServiceRequestService,
)

from utils.enums import (
    ServiceRequestStatus,
    ServiceRequestType,
    UserRole,
)


router = APIRouter(
    prefix="/service-requests",
    tags=["Service Requests"],
)

service = ServiceRequestService()


# ============================================================
# CREATE
# ============================================================


@router.post(
    "",
    response_model=ServiceRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service_request(
    data: ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return service.create_request(
        db,
        data,
        current_user,
    )


# ============================================================
# GET ALL
# ============================================================


@router.get(
    "",
    response_model=list[ServiceRequestResponse],
)
def get_service_requests(
    customer_id: int | None = Query(
        default=None,
    ),
    request_type: ServiceRequestType | None = Query(
        default=None,
    ),
    request_status: ServiceRequestStatus | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return service.get_requests(
        db,
        current_user,
        customer_id=customer_id,
        request_type=request_type,
        request_status=request_status,
    )


# ============================================================
# GET ONE
# ============================================================


@router.get(
    "/{request_id}",
    response_model=ServiceRequestResponse,
)
def get_service_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return service.get_request(
        db,
        request_id,
        current_user,
    )


# ============================================================
# UPDATE STATUS
# ============================================================


@router.patch(
    "/{request_id}/status",
    response_model=ServiceRequestResponse,
)
def update_service_request_status(
    request_id: int,
    data: ServiceRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
        )
    ),
):
    return service.update_status(
        db,
        request_id,
        data,
        current_user,
    )


# ============================================================
# HISTORY
# ============================================================


@router.get(
    "/{request_id}/history",
    response_model=list[
        ServiceRequestHistoryResponse
    ],
)
def get_service_request_history(
    request_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return service.get_history(
        db,
        request_id,
        current_user,
    )