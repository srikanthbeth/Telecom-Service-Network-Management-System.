from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user,
    require_roles,
)
from db.database import get_db
from models.user import User
from schemas.plan import (
    PlanComparisonResponse,
    PlanCreate,
    PlanResponse,
    PlanUpdate,
)
from services.plan_service import PlanService
from utils.enums import PlanStatus, PlanType, UserRole


router = APIRouter(
    prefix="/plans",
    tags=["Plans"],
)


@router.post(
    "",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_plan(
    data: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = PlanService(db)

    return service.create(data)


@router.get(
    "",
    response_model=list[PlanResponse],
)
def list_plans(
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    plan_type: PlanType | None = None,
    status: PlanStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = PlanService(db)

    return service.list(
        search=search,
        plan_type=plan_type,
        status=status,
    )


@router.get(
    "/compare",
    response_model=list[PlanComparisonResponse],
)
def compare_plans(
    plan_ids: list[int] = Query(
        min_length=2,
        max_length=5,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = PlanService(db)

    return service.compare(
        plan_ids
    )


@router.get(
    "/{plan_id}",
    response_model=PlanResponse,
)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = PlanService(db)

    return service.get(plan_id)


@router.patch(
    "/{plan_id}",
    response_model=PlanResponse,
)
def update_plan(
    plan_id: int,
    data: PlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = PlanService(db)

    return service.update(
        plan_id,
        data,
    )


@router.patch(
    "/{plan_id}/activate",
    response_model=PlanResponse,
)
def activate_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = PlanService(db)

    return service.activate(
        plan_id
    )


@router.patch(
    "/{plan_id}/deactivate",
    response_model=PlanResponse,
)
def deactivate_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = PlanService(db)

    return service.deactivate(
        plan_id
    )