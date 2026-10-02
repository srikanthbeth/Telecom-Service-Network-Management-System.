from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.customer import Customer
from repositories.customer_history_repository import (
    CustomerHistoryRepository,
)
from repositories.customer_repository import CustomerRepository
from schemas.customer import CustomerCreate, CustomerUpdate
from utils.enums import KYCStatus, UserRole


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CustomerRepository(db)
        self.history_repository = CustomerHistoryRepository(db)

    def create(
        self,
        data: CustomerCreate,
        changed_by: int,
    ) -> Customer:

        user = self.repository.get_user(
            data.user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.role != UserRole.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer profile can only be created for Customer users",
            )

        existing_user = (
            self.repository.get_by_user_id(
                data.user_id
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer profile already exists",
            )

        existing_number = (
            self.repository.get_by_customer_number(
                data.customer_number
            )
        )

        if existing_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer number already exists",
            )

        customer = Customer(
            user_id=data.user_id,
            customer_number=data.customer_number,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            country=data.country,
            kyc_status=data.kyc_status,
            is_active=True,
        )

        customer = self.repository.create(customer)

        self.history_repository.create(
            customer_id=customer.id,
            changed_by=changed_by,
            action="CUSTOMER_CREATED",
            description="Customer profile created",
            previous_value=None,
            new_value={
                "customer_number": customer.customer_number,
                "kyc_status": customer.kyc_status.value,
                "is_active": customer.is_active,
            },
        )

        return customer

    def get(
        self,
        customer_id: int,
    ) -> Customer:

        customer = self.repository.get_by_id(
            customer_id
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        return customer

    def update(
        self,
        customer_id: int,
        data: CustomerUpdate,
        changed_by: int,
    ) -> Customer:

        customer = self.get(customer_id)

        update_data = data.model_dump(
            exclude_unset=True
        )

        if not update_data:
            return customer

        previous_values = {}

        for field in update_data:
            old_value = getattr(
                customer,
                field,
            )

            if hasattr(old_value, "value"):
                old_value = old_value.value

            previous_values[field] = old_value

        for field, value in update_data.items():
            setattr(
                customer,
                field,
                value,
            )

        customer = self.repository.update(
            customer
        )

        new_values = {}

        for field in update_data:
            new_value = getattr(
                customer,
                field,
            )

            if hasattr(new_value, "value"):
                new_value = new_value.value

            new_values[field] = new_value

        self.history_repository.create(
            customer_id=customer.id,
            changed_by=changed_by,
            action="CUSTOMER_UPDATED",
            description="Customer profile updated",
            previous_value=previous_values,
            new_value=new_values,
        )

        return customer

    def activate(
        self,
        customer_id: int,
        changed_by: int,
    ) -> Customer:

        customer = self.get(customer_id)

        user = self.repository.get_user(
            customer.user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        previous_value = {
            "customer_is_active": customer.is_active,
            "user_is_active": user.is_active,
        }

        customer.is_active = True
        user.is_active = True

        self.db.commit()
        self.db.refresh(customer)

        self.history_repository.create(
            customer_id=customer.id,
            changed_by=changed_by,
            action="CUSTOMER_ACTIVATED",
            description="Customer account activated",
            previous_value=previous_value,
            new_value={
                "customer_is_active": True,
                "user_is_active": True,
            },
        )

        return customer

    def deactivate(
        self,
        customer_id: int,
        changed_by: int,
    ) -> Customer:

        customer = self.get(customer_id)

        user = self.repository.get_user(
            customer.user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        previous_value = {
            "customer_is_active": customer.is_active,
            "user_is_active": user.is_active,
        }

        customer.is_active = False
        user.is_active = False

        self.db.commit()
        self.db.refresh(customer)

        self.history_repository.create(
            customer_id=customer.id,
            changed_by=changed_by,
            action="CUSTOMER_DEACTIVATED",
            description="Customer account deactivated",
            previous_value=previous_value,
            new_value={
                "customer_is_active": False,
                "user_is_active": False,
            },
        )

        return customer

    def history(
        self,
        customer_id: int,
    ):

        self.get(customer_id)

        return self.history_repository.get_by_customer_id(
            customer_id
        )

    def list(
        self,
        search: str | None = None,
        kyc_status: KYCStatus | None = None,
        is_active: bool | None = None,
    ) -> list[Customer]:

        return self.repository.list(
            search=search,
            kyc_status=kyc_status,
            is_active=is_active,
        )