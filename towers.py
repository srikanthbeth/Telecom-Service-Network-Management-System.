from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.tower import TowerStatus, TowerType
from schemas.tower import (
    TowerCreate,
    TowerResponse,
    TowerStatusUpdate,
    TowerUpdate,
)
from services.tower_service import TowerService

router = APIRouter(
    prefix="/towers",
    tags=["Network Towers"],
)


@router.post(
    "",
    response_model=TowerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tower(
    data: TowerCreate,
    db: Session = Depends(get_db),
):
    service = TowerService(db)

    return service.create_tower(data)


@router.get(
    "",
    response_model=list[TowerResponse],
)
def list_towers(
    status_value: TowerStatus | None = Query(
        default=None,
        alias="status",
    ),
    tower_type: TowerType | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    service = TowerService(db)

    return service.list_towers(
        status_value=status_value,
        tower_type=tower_type,
        search=search,
    )


@router.get(
    "/{tower_id}",
    response_model=TowerResponse,
)
def get_tower(
    tower_id: int,
    db: Session = Depends(get_db),
):
    service = TowerService(db)

    return service.get_tower(tower_id)


@router.put(
    "/{tower_id}",
    response_model=TowerResponse,
)
def update_tower(
    tower_id: int,
    data: TowerUpdate,
    db: Session = Depends(get_db),
):
    service = TowerService(db)

    return service.update_tower(
        tower_id,
        data,
    )


@router.patch(
    "/{tower_id}/status",
    response_model=TowerResponse,
)
def update_tower_status(
    tower_id: int,
    data: TowerStatusUpdate,
    db: Session = Depends(get_db),
):
    service = TowerService(db)

    return service.update_status(
        tower_id,
        data.status,
    )


@router.delete(
    "/{tower_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tower(
    tower_id: int,
    db: Session = Depends(get_db),
):
    service = TowerService(db)

    service.delete_tower(tower_id)

    return None