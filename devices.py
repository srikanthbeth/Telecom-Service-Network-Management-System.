from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, require_roles
from db.database import get_db
from schemas.device import (
    DeviceCreate,
    DeviceResponse,
    DeviceSIMAssignRequest,
    DeviceSIMMappingResponse,
    DeviceUpdate,
)
from services.device_service import DeviceService
from utils.enums import (
    DeviceStatus,
    DeviceType,
    UserRole,
)


router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
)

service = DeviceService()


# =========================================================
# CREATE DEVICE
# =========================================================

@router.post(
    "",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    device = service.create(
        db=db,
        imei=data.imei,
        model=data.model,
        manufacturer=data.manufacturer,
        device_type=data.device_type,
        customer_id=data.customer_id,
    )

    db.commit()
    db.refresh(device)

    return device


# =========================================================
# LIST DEVICES
# =========================================================

@router.get(
    "",
    response_model=list[DeviceResponse],
)
def list_devices(
    search: str | None = Query(default=None),
    device_type: DeviceType | None = Query(default=None),
    status: DeviceStatus | None = Query(default=None),
    customer_id: int | None = Query(
        default=None,
        gt=0,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.list(
        db=db,
        search=search,
        device_type=device_type,
        status=status,
        customer_id=customer_id,
    )


# =========================================================
# GET DEVICE
# =========================================================

@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get(
        db,
        device_id,
    )


# =========================================================
# UPDATE DEVICE
# =========================================================

@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
)
def update_device(
    device_id: int,
    data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    device = service.update(
        db=db,
        device_id=device_id,
        imei=data.imei,
        model=data.model,
        manufacturer=data.manufacturer,
        device_type=data.device_type,
        customer_id=data.customer_id,
    )

    db.commit()
    db.refresh(device)

    return device


# =========================================================
# ACTIVATE DEVICE
# =========================================================

@router.patch(
    "/{device_id}/activate",
    response_model=DeviceResponse,
)
def activate_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    device = service.activate(
        db,
        device_id,
    )

    db.commit()
    db.refresh(device)

    return device


# =========================================================
# DEACTIVATE DEVICE
# =========================================================

@router.patch(
    "/{device_id}/deactivate",
    response_model=DeviceResponse,
)
def deactivate_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    device = service.deactivate(
        db,
        device_id,
    )

    db.commit()
    db.refresh(device)

    return device


# =========================================================
# BLOCK DEVICE
# =========================================================

@router.patch(
    "/{device_id}/block",
    response_model=DeviceResponse,
)
def block_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    device = service.block(
        db,
        device_id,
    )

    db.commit()
    db.refresh(device)

    return device


# =========================================================
# MARK DEVICE LOST
# =========================================================

@router.patch(
    "/{device_id}/lost",
    response_model=DeviceResponse,
)
def mark_device_lost(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    device = service.mark_lost(
        db,
        device_id,
    )

    db.commit()
    db.refresh(device)

    return device


# =========================================================
# ASSIGN SIM
# =========================================================

@router.post(
    "/{device_id}/sim",
    response_model=DeviceSIMMappingResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_sim(
    device_id: int,
    data: DeviceSIMAssignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    mapping = service.assign_sim(
        db=db,
        device_id=device_id,
        sim_id=data.sim_id,
    )

    db.commit()
    db.refresh(mapping)

    return mapping


# =========================================================
# UNASSIGN SIM
# =========================================================

@router.delete(
    "/{device_id}/sim",
    response_model=DeviceSIMMappingResponse,
)
def unassign_sim(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    mapping = service.unassign_sim(
        db,
        device_id,
    )

    db.commit()
    db.refresh(mapping)

    return mapping


# =========================================================
# CURRENT SIM
# =========================================================

@router.get(
    "/{device_id}/sim",
    response_model=DeviceSIMMappingResponse,
)
def get_current_sim(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get_current_sim(
        db,
        device_id,
    )


# =========================================================
# SIM ASSIGNMENT HISTORY
# =========================================================

@router.get(
    "/{device_id}/sim-history",
    response_model=list[DeviceSIMMappingResponse],
)
def get_sim_history(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.sim_history(
        db,
        device_id,
    )