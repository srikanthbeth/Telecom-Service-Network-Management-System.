from sqlalchemy import select
from sqlalchemy.orm import Session

from models.service_request import ServiceRequest
from models.service_request_history import (
    ServiceRequestHistory,
)

from utils.enums import ServiceRequestStatus


class ServiceRequestRepository:

    # =========================================================
    # SERVICE REQUEST
    # =========================================================

    def create(
        self,
        db: Session,
        service_request: ServiceRequest,
    ):
        db.add(service_request)
        db.flush()

        return service_request

    def get_by_id(
        self,
        db: Session,
        request_id: int,
    ):
        return db.get(
            ServiceRequest,
            request_id,
        )

    def get_by_request_number(
        self,
        db: Session,
        request_number: str,
    ):
        statement = (
            select(ServiceRequest)
            .where(
                ServiceRequest.request_number
                == request_number
            )
        )

        return db.scalar(statement)

    def get_all(
        self,
        db: Session,
        customer_id: int | None = None,
        request_type=None,
        status_value: ServiceRequestStatus | None = None,
    ):
        statement = select(
            ServiceRequest
        )

        if customer_id is not None:
            statement = statement.where(
                ServiceRequest.customer_id
                == customer_id
            )

        if request_type is not None:
            statement = statement.where(
                ServiceRequest.request_type
                == request_type
            )

        if status_value is not None:
            statement = statement.where(
                ServiceRequest.status
                == status_value
            )

        statement = statement.order_by(
            ServiceRequest.created_at.desc()
        )

        return list(
            db.scalars(statement).all()
        )

    # =========================================================
    # HISTORY
    # =========================================================

    def create_history(
        self,
        db: Session,
        history: ServiceRequestHistory,
    ):
        db.add(history)
        db.flush()

        return history

    def get_history(
        self,
        db: Session,
        request_id: int,
    ):
        statement = (
            select(ServiceRequestHistory)
            .where(
                ServiceRequestHistory.service_request_id
                == request_id
            )
            .order_by(
                ServiceRequestHistory.changed_at.asc(),
                ServiceRequestHistory.id.asc(),
            )
        )

        return list(
            db.scalars(statement).all()
        )