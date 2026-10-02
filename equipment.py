
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from db.database import get_db
from schemas.network_equipment import (
    NetworkEquipmentCreate,
    NetworkEquipmentHealthUpdate,
    NetworkEquipmentResponse,
    NetworkEquipmentStatusUpdate,
    NetworkEquipmentUpdate,
)
from services.network_equipment_service import (
    NetworkEquipmentService,
)
from utils.enums import (
    EquipmentHealth,
    EquipmentType,
    NetworkStatus,
)


router = APIRouter(
    prefix="/equipment",
    tags=["Network Equipment"],
)

service = NetworkEquipmentService()


# =========================================================
# CREATE
# =========================================================

@router.post(
    "",
    response_model=NetworkEquipmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_equipment(
    data: NetworkEquipmentCreate,
    db: Session = Depends(get_db),
):
    return service.create(
        db=db,
        equipment_code=data.equipment_code,
        equipment_name=data.equipment_name,
        equipment_type=data.equipment_type,
        manufacturer=data.manufacturer,
        model_number=data.model_number,
        serial_number=data.serial_number,
        tower_id=data.tower_id,
        location=data.location,
        installation_date=data.installation_date,
        maintenance_schedule=data.maintenance_schedule,
        cpu_usage=data.cpu_usage,
        memory_usage=data.memory_usage,
        network_status=data.network_status,
        health_status=data.health_status,
        last_heartbeat=data.last_heartbeat,
        downtime_minutes=data.downtime_minutes,
        description=data.description,
        created_by=None,
    )


# =========================================================
# LIST
# =========================================================

@router.get(
    "",
    response_model=list[NetworkEquipmentResponse],
)
def list_equipment(
    equipment_type: EquipmentType | None = Query(
        default=None
    ),
    network_status: NetworkStatus | None = Query(
        default=None
    ),
    health_status: EquipmentHealth | None = Query(
        default=None
    ),
    tower_id: int | None = Query(
        default=None,
        gt=0,
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
    ),
    db: Session = Depends(get_db),
):
    return service.list(
        db=db,
        equipment_type=equipment_type,
        network_status=network_status,
        health_status=health_status,
        tower_id=tower_id,
        search=search,
    )


# =========================================================
# GET
# =========================================================

@router.get(
    "/{equipment_id}",
    response_model=NetworkEquipmentResponse,
)
def get_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
):
    return service.get(
        db,
        equipment_id,
    )


# =========================================================
# UPDATE
# =========================================================

@router.put(
    "/{equipment_id}",
    response_model=NetworkEquipmentResponse,
)
def update_equipment(
    equipment_id: int,
    data: NetworkEquipmentUpdate,
    db: Session = Depends(get_db),
):
    values = data.model_dump(
        exclude_unset=True
    )

    return service.update(
        db=db,
        equipment_id=equipment_id,
        values=values,
    )


# =========================================================
# UPDATE NETWORK STATUS
# =========================================================

@router.patch(
    "/{equipment_id}/status",
    response_model=NetworkEquipmentResponse,
)
def update_equipment_status(
    equipment_id: int,
    data: NetworkEquipmentStatusUpdate,
    db: Session = Depends(get_db),
):
    return service.update_status(
        db=db,
        equipment_id=equipment_id,
        network_status=data.network_status,
    )


# =========================================================
# UPDATE HEALTH
# =========================================================

@router.patch(
    "/{equipment_id}/health",
    response_model=NetworkEquipmentResponse,
)
def update_equipment_health(
    equipment_id: int,
    data: NetworkEquipmentHealthUpdate,
    db: Session = Depends(get_db),
):
    return service.update_health(
        db=db,
        equipment_id=equipment_id,
        health_status=data.health_status,
    )


# =========================================================
# DELETE
# =========================================================

@router.delete(
    "/{equipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
):
    service.delete(
        db=db,
        equipment_id=equipment_id,
    )

    return None

