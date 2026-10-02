from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user,
    require_roles,
)
from db.database import get_db
from models.user import User
from schemas.sim import (
    SIMCreate,
    SIMReplaceRequest,
    SIMResponse,
    SIMUpdate,
)
from schemas.sim_replacement_history import (
    SIMReplacementHistoryResponse,
)
from services.sim_service import SIMService
from utils.enums import SIMStatus, SIMType, UserRole


router = APIRouter(
    prefix="/sims",
    tags=["SIMs"],
)


@router.post(
    "",
    response_model=SIMResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sim(
    data: SIMCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = SIMService(db)

    return service.create(data)


@router.get(
    "",
    response_model=list[SIMResponse],
)
def list_sims(
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    sim_type: SIMType | None = None,
    status: SIMStatus | None = None,
    customer_id: int | None = Query(
        default=None,
        gt=0,
    ),
    plan_id: int | None = Query(
        default=None,
        gt=0,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = SIMService(db)

    return service.list(
        search=search,
        sim_type=sim_type,
        status=status,
        customer_id=customer_id,
        plan_id=plan_id,
    )


@router.get(
    "/{sim_id}",
    response_model=SIMResponse,
)
def get_sim(
    sim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = SIMService(db)

    return service.get(sim_id)


@router.patch(
    "/{sim_id}",
    response_model=SIMResponse,
)
def update_sim(
    sim_id: int,
    data: SIMUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = SIMService(db)

    return service.update(
        sim_id,
        data,
    )


@router.patch(
    "/{sim_id}/activate",
    response_model=SIMResponse,
)
def activate_sim(
    sim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = SIMService(db)

    return service.activate(sim_id)


@router.patch(
    "/{sim_id}/suspend",
    response_model=SIMResponse,
)
def suspend_sim(
    sim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = SIMService(db)

    return service.suspend(sim_id)


@router.patch(
    "/{sim_id}/lost",
    response_model=SIMResponse,
)
def mark_sim_lost(
    sim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = SIMService(db)

    return service.mark_lost(sim_id)


@router.patch(
    "/{sim_id}/block",
    response_model=SIMResponse,
)
def block_sim(
    sim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = SIMService(db)

    return service.block(sim_id)


@router.patch(
    "/{sim_id}/deactivate",
    response_model=SIMResponse,
)
def deactivate_sim(
    sim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = SIMService(db)

    return service.deactivate(sim_id)


@router.post(
    "/{sim_id}/replace",
    response_model=SIMResponse,
)
def replace_sim(
    sim_id: int,
    data: SIMReplaceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    service = SIMService(db)

    return service.replace(
        sim_id,
        data,
        replaced_by=current_user.id,
    )


@router.get(
    "/{sim_id}/replacement-history",
    response_model=list[
        SIMReplacementHistoryResponse
    ],
)
def get_replacement_history(
    sim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = SIMService(db)

    return service.replacement_history(
        sim_id
    )