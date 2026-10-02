from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from db.database import get_db
from schemas.network_outage import (
    AffectedCustomerResponse,
    NetworkOutageCreate,
    NetworkOutageResolve,
    NetworkOutageResponse,
    NetworkOutageUpdate,
)
from services.network_outage_service import (
    NetworkOutageService,
)
from utils.enums import OutageSeverity


router = APIRouter(
    prefix="/outages",
    tags=["Network Outages"],
)

service = NetworkOutageService()


def build_response(
    db: Session,
    outage,
) -> NetworkOutageResponse:

    tower_ids = service.repository.get_tower_ids(
        db,
        outage.id,
    )

    customer_ids = service.affected_customers(
        db,
        outage.id,
    )

    return NetworkOutageResponse(
        id=outage.id,
        outage_code=outage.outage_code,
        outage_type=outage.outage_type,
        description=outage.description,
        severity=outage.severity,
        start_time=outage.start_time,
        expected_resolution=outage.expected_resolution,
        actual_resolution=outage.actual_resolution,
        created_at=outage.created_at,
        updated_at=outage.updated_at,
        tower_ids=tower_ids,
        affected_customer_ids=customer_ids,
    )


@router.post(
    "",
    response_model=NetworkOutageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_outage(
    data: NetworkOutageCreate,
    db: Session = Depends(get_db),
):
    outage = service.create(
        db,
        data,
    )

    return build_response(
        db,
        outage,
    )


@router.get(
    "",
    response_model=list[NetworkOutageResponse],
)
def list_outages(
    severity: OutageSeverity | None = Query(default=None),
    outage_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    outages = service.get_all(
        db=db,
        severity=severity,
        outage_type=outage_type,
    )

    return [
        build_response(db, outage)
        for outage in outages
    ]

@router.get(
    "/{outage_id}",
    response_model=NetworkOutageResponse,
)
def get_outage(
    outage_id: int,
    db: Session = Depends(get_db),
):
    outage = service.get(
        db,
        outage_id,
    )

    return build_response(
        db,
        outage,
    )


@router.put(
    "/{outage_id}",
    response_model=NetworkOutageResponse,
)
def update_outage(
    outage_id: int,
    data: NetworkOutageUpdate,
    db: Session = Depends(get_db),
):
    outage = service.update(
        db,
        outage_id,
        data,
    )

    return build_response(
        db,
        outage,
    )


@router.patch(
    "/{outage_id}/resolve",
    response_model=NetworkOutageResponse,
)
def resolve_outage(
    outage_id: int,
    data: NetworkOutageResolve,
    db: Session = Depends(get_db),
):
    outage = service.resolve(
        db,
        outage_id,
        data,
    )

    return build_response(
        db,
        outage,
    )


@router.get(
    "/{outage_id}/affected-customers",
    response_model=list[AffectedCustomerResponse],
)
def get_affected_customers(
    outage_id: int,
    db: Session = Depends(get_db),
):
    customer_ids = service.affected_customers(
        db,
        outage_id,
    )

    return [
        AffectedCustomerResponse(
            customer_id=customer_id
        )
        for customer_id in customer_ids
    ]


@router.delete(
    "/{outage_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_outage(
    outage_id: int,
    db: Session = Depends(get_db),
):
    service.delete(
        db,
        outage_id,
    )