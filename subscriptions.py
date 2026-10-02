from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user,
    require_roles,
)
from db.database import get_db

from schemas.subscription import (
    SubscriptionCreate,
    SubscriptionHistoryResponse,
    SubscriptionPlanChange,
    SubscriptionRenew,
    SubscriptionResponse,
)

from services.subscription_service import (
    SubscriptionService,
)

from utils.enums import (
    SubscriptionStatus,
    UserRole,
)


router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"],
)

service = SubscriptionService()


# =========================================================
# CREATE
# =========================================================

@router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subscription(
    data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    return service.create(
        db=db,
        customer_id=data.customer_id,
        sim_id=data.sim_id,
        plan_id=data.plan_id,
        start_date=data.start_date,
        end_date=data.end_date,
        changed_by=current_user.id,
    )


# =========================================================
# LIST
# =========================================================

@router.get(
    "",
    response_model=list[SubscriptionResponse],
)
def list_subscriptions(
    customer_id: int | None = Query(
        default=None,
        gt=0,
    ),
    sim_id: int | None = Query(
        default=None,
        gt=0,
    ),
    plan_id: int | None = Query(
        default=None,
        gt=0,
    ),
    subscription_status: SubscriptionStatus | None = Query(
        default=None,
        alias="status",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.list(
        db=db,
        customer_id=customer_id,
        sim_id=sim_id,
        plan_id=plan_id,
        status=subscription_status,
    )


# =========================================================
# GET
# =========================================================

@router.get(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
)
def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get(
        db,
        subscription_id,
    )


# =========================================================
# UPGRADE
# =========================================================

@router.patch(
    "/{subscription_id}/upgrade",
    response_model=SubscriptionResponse,
)
def upgrade_subscription(
    subscription_id: int,
    data: SubscriptionPlanChange,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    return service.upgrade(
        db=db,
        subscription_id=subscription_id,
        plan_id=data.plan_id,
        changed_by=current_user.id,
    )


# =========================================================
# DOWNGRADE
# =========================================================

@router.patch(
    "/{subscription_id}/downgrade",
    response_model=SubscriptionResponse,
)
def downgrade_subscription(
    subscription_id: int,
    data: SubscriptionPlanChange,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    return service.downgrade(
        db=db,
        subscription_id=subscription_id,
        plan_id=data.plan_id,
        changed_by=current_user.id,
    )


# =========================================================
# RENEW
# =========================================================

@router.patch(
    "/{subscription_id}/renew",
    response_model=SubscriptionResponse,
)
def renew_subscription(
    subscription_id: int,
    data: SubscriptionRenew,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    return service.renew(
        db=db,
        subscription_id=subscription_id,
        end_date=data.end_date,
        changed_by=current_user.id,
    )


# =========================================================
# SUSPEND
# =========================================================

@router.patch(
    "/{subscription_id}/suspend",
    response_model=SubscriptionResponse,
)
def suspend_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
        )
    ),
):
    return service.suspend(
        db=db,
        subscription_id=subscription_id,
        changed_by=current_user.id,
    )


# =========================================================
# REACTIVATE
# =========================================================

@router.patch(
    "/{subscription_id}/reactivate",
    response_model=SubscriptionResponse,
)
def reactivate_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
        )
    ),
):
    return service.reactivate(
        db=db,
        subscription_id=subscription_id,
        changed_by=current_user.id,
    )


# =========================================================
# CANCEL
# =========================================================

@router.patch(
    "/{subscription_id}/cancel",
    response_model=SubscriptionResponse,
)
def cancel_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    return service.cancel(
        db=db,
        subscription_id=subscription_id,
        changed_by=current_user.id,
    )


# =========================================================
# HISTORY
# =========================================================

@router.get(
    "/{subscription_id}/history",
    response_model=list[SubscriptionHistoryResponse],
)
def subscription_history(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.history(
        db,
        subscription_id,
    )