from sqlalchemy import select
from sqlalchemy.orm import Session

from models.customer import Customer
from models.user import User
from utils.enums import KYCStatus


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        customer_id: int,
    ) -> Customer | None:
        return self.db.get(
            Customer,
            customer_id,
        )

    def get_by_user_id(
        self,
        user_id: int,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.user_id == user_id
        )

        return self.db.scalar(statement)

    def get_by_customer_number(
        self,
        customer_number: str,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.customer_number
            == customer_number
        )

        return self.db.scalar(statement)

    def get_user(
        self,
        user_id: int,
    ) -> User | None:
        return self.db.get(
            User,
            user_id,
        )

    def create(
        self,
        customer: Customer,
    ) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        return customer

    def update(
        self,
        customer: Customer,
    ) -> Customer:
        self.db.commit()
        self.db.refresh(customer)

        return customer

    def list(
        self,
        search: str | None = None,
        kyc_status: KYCStatus | None = None,
        is_active: bool | None = None,
    ) -> list[Customer]:

        statement = (
            select(Customer)
            .join(User, Customer.user_id == User.id)
        )

        if search:
            search_value = f"%{search.lower()}%"

            statement = statement.where(
                (
                    User.full_name.ilike(
                        search_value
                    )
                )
                |
                (
                    User.email.ilike(
                        search_value
                    )
                )
                |
                (
                    Customer.customer_number.ilike(
                        search_value
                    )
                )
            )

        if kyc_status:
            statement = statement.where(
                Customer.kyc_status == kyc_status
            )

        if is_active is not None:
            statement = statement.where(
                Customer.is_active == is_active
            )

        statement = statement.order_by(
            Customer.id.desc()
        )

        return list(
            self.db.scalars(statement).all()
        )