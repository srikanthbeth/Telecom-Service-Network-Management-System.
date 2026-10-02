from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.customer import Customer
from models.service_request import ServiceRequest
from models.service_request_history import (
    ServiceRequestHistory,
)
from models.user import User

from repositories.service_request_repository import (
    ServiceRequestRepository,
)

from schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestStatusUpdate,
)

from utils.enums import (
    ServiceRequestStatus,
    UserRole,
)


class ServiceRequestService:

    def __init__(self):
        self.repository = (
            ServiceRequestRepository()
        )

    # =========================================================
    # HELPERS
    # =========================================================

    def _generate_request_number(
        self,
        db: Session,
    ):
        while True:
            last_request = (
                db.query(ServiceRequest)
                .order_by(
                    ServiceRequest.id.desc()
                )
                .first()
            )

            if last_request:
                number = last_request.id + 1
            else:
                number = 1

            request_number = (
                f"SR-{number:06d}"
            )

            existing = (
                self.repository
                .get_by_request_number(
                    db,
                    request_number,
                )
            )

            if not existing:
                return request_number

            number += 1

    def _value(self, value):
        if hasattr(value, "value"):
            return value.value

        return value

    # =========================================================
    # CREATE REQUEST
    # =========================================================

    def create_request(
        self,
        db: Session,
        data: ServiceRequestCreate,
        current_user: User,
    ):
        customer = db.get(
            Customer,
            data.customer_id,
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer account is inactive",
            )

        # -----------------------------------------------------
        # Customer can create only their own request.
        # Staff/admin roles can create for any customer.
        # -----------------------------------------------------

        if (
            self._value(current_user.role)
            == self._value(UserRole.CUSTOMER)
            and customer.user_id
            != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers can create requests only for themselves",
            )

        request_number = (
            self._generate_request_number(
                db
            )
        )

        service_request = ServiceRequest(
            request_number=request_number,
            customer_id=data.customer_id,
            request_type=data.request_type,
            status=ServiceRequestStatus.PENDING,
            reason=data.reason,
            description=data.description,
            created_by=current_user.id,
        )

        self.repository.create(
            db,
            service_request,
        )

        # -----------------------------------------------------
        # First history record
        # -----------------------------------------------------

        history = ServiceRequestHistory(
            service_request_id=service_request.id,
            old_status=None,
            new_status=ServiceRequestStatus.PENDING,
            remarks="Service request created",
            changed_by=current_user.id,
        )

        self.repository.create_history(
            db,
            history,
        )

        db.commit()
        db.refresh(service_request)

        return service_request

    # =========================================================
    # GET REQUEST
    # =========================================================

    def get_request(
        self,
        db: Session,
        request_id: int,
        current_user: User | None = None,
    ):
        service_request = (
            self.repository.get_by_id(
                db,
                request_id,
            )
        )

        if not service_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service request not found",
            )

        if current_user:
            self._check_access(
                db,
                service_request,
                current_user,
            )

        return service_request

    # =========================================================
    # GET ALL
    # =========================================================

    def get_requests(
        self,
        db: Session,
        current_user: User,
        customer_id: int | None = None,
        request_type=None,
        request_status=None,
    ):
        is_customer = (
            self._value(current_user.role)
            == self._value(UserRole.CUSTOMER)
        )

        if is_customer:
            customer = (
                db.query(Customer)
                .filter(
                    Customer.user_id
                    == current_user.id
                )
                .first()
            )

            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer record not found",
                )

            customer_id = customer.id

        return self.repository.get_all(
            db,
            customer_id=customer_id,
            request_type=request_type,
            status_value=request_status,
        )

    # =========================================================
    # UPDATE STATUS
    # =========================================================

    def update_status(
        self,
        db: Session,
        request_id: int,
        data: ServiceRequestStatusUpdate,
        current_user: User,
    ):
        service_request = (
            self.repository.get_by_id(
                db,
                request_id,
            )
        )

        if not service_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service request not found",
            )

        # -----------------------------------------------------
        # Customers cannot change request status.
        # -----------------------------------------------------

        if (
            self._value(current_user.role)
            == self._value(UserRole.CUSTOMER)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers cannot update service request status",
            )

        current_status = service_request.status
        new_status = data.status

        # -----------------------------------------------------
        # Same status is not allowed.
        # -----------------------------------------------------

        if current_status == new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service request already has this status",
            )

        # -----------------------------------------------------
        # Validate status transition.
        # -----------------------------------------------------

        allowed_transitions = {
            ServiceRequestStatus.PENDING: {
                ServiceRequestStatus.IN_PROGRESS,
                ServiceRequestStatus.CANCELLED,
                ServiceRequestStatus.REJECTED,
            },
            ServiceRequestStatus.IN_PROGRESS: {
                ServiceRequestStatus.APPROVED,
                ServiceRequestStatus.REJECTED,
                ServiceRequestStatus.CANCELLED,
            },
            ServiceRequestStatus.APPROVED: {
                ServiceRequestStatus.IN_PROGRESS,
                ServiceRequestStatus.COMPLETED,
                ServiceRequestStatus.CANCELLED,
            },
            ServiceRequestStatus.REJECTED: set(),
            ServiceRequestStatus.COMPLETED: set(),
            ServiceRequestStatus.CANCELLED: set(),
        }

        allowed = allowed_transitions.get(
            current_status,
            set(),
        )

        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid status transition from "
                    f"{self._value(current_status)} to "
                    f"{self._value(new_status)}"
                ),
            )

        # -----------------------------------------------------
        # Update request
        # -----------------------------------------------------

        service_request.status = new_status

        if (
            new_status
            == ServiceRequestStatus.COMPLETED
        ):
            service_request.completed_at = (
                datetime.now(timezone.utc)
            )
        else:
            service_request.completed_at = None

        # -----------------------------------------------------
        # Create history record
        # -----------------------------------------------------

        history = ServiceRequestHistory(
            service_request_id=service_request.id,
            old_status=current_status,
            new_status=new_status,
            remarks=data.remarks,
            changed_by=current_user.id,
        )

        self.repository.create_history(
            db,
            history,
        )

        db.commit()
        db.refresh(service_request)

        return service_request

    # =========================================================
    # HISTORY
    # =========================================================

    def get_history(
        self,
        db: Session,
        request_id: int,
        current_user: User,
    ):
        service_request = (
            self.repository.get_by_id(
                db,
                request_id,
            )
        )

        if not service_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service request not found",
            )

        self._check_access(
            db,
            service_request,
            current_user,
        )

        return self.repository.get_history(
            db,
            request_id,
        )

    # =========================================================
    # ACCESS CONTROL
    # =========================================================

    def _check_access(
        self,
        db: Session,
        service_request: ServiceRequest,
        current_user: User,
    ):
        role = self._value(
            current_user.role
        )

        staff_roles = {
            self._value(UserRole.SUPER_ADMIN),
            self._value(UserRole.OPERATIONS_MANAGER),
            self._value(UserRole.SUPPORT_AGENT),
        }

        if role in staff_roles:
            return

        if role == self._value(
            UserRole.CUSTOMER
        ):
            customer = db.get(
                Customer,
                service_request.customer_id,
            )

            if (
                not customer
                or customer.user_id
                != current_user.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this service request",
                )

            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this service request",
        )