from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user,
    require_roles,
)
from db.database import get_db
from models.customer import Customer
from models.user import User
from schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)
from schemas.customer_history import (
    CustomerHistoryResponse,
)
from services.customer_service import CustomerService
from utils.enums import KYCStatus, UserRole


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = CustomerService(db)

    return service.create(
        data,
        changed_by=current_user.id,
    )


@router.get(
    "",
    response_model=list[CustomerResponse],
)
def list_customers(
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    kyc_status: KYCStatus | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = CustomerService(db)

    return service.list(
        search=search,
        kyc_status=kyc_status,
        is_active=is_active,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = CustomerService(db)

    return service.get(customer_id)


@router.get(
    "/{customer_id}/history",
    response_model=list[CustomerHistoryResponse],
)
def get_customer_history(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = CustomerService(db)

    return service.history(
        customer_id
    )


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = CustomerService(db)

    return service.update(
        customer_id,
        data,
        changed_by=current_user.id,
    )


@router.patch(
    "/{customer_id}/activate",
    response_model=CustomerResponse,
)
def activate_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = CustomerService(db)

    return service.activate(
        customer_id,
        changed_by=current_user.id,
    )


@router.patch(
    "/{customer_id}/deactivate",
    response_model=CustomerResponse,
)
def deactivate_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = CustomerService(db)

    return service.deactivate(
        customer_id,
        changed_by=current_user.id,
    )