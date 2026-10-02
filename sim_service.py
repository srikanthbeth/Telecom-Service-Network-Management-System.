from datetime import date
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.sim import SIM
from repositories.customer_repository import (
    CustomerRepository,
)
from repositories.plan_repository import (
    PlanRepository,
)
from repositories.sim_repository import (
    SIMRepository,
)
from repositories.sim_replacement_history_repository import (
    SIMReplacementHistoryRepository,
)
from schemas.sim import SIMCreate, SIMReplaceRequest, SIMUpdate
from utils.enums import PlanStatus, SIMStatus


class SIMService:
    def __init__(self, db: Session):
        self.db = db

        self.repository = SIMRepository(db)

        self.customer_repository = CustomerRepository(
            db
        )

        self.plan_repository = PlanRepository(
            db
        )

        self.history_repository = (
            SIMReplacementHistoryRepository(db)
        )

    def _validate_customer(
        self,
        customer_id: int,
    ):
        customer = (
            self.customer_repository.get_by_id(
                customer_id
            )
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

        return customer

    def _validate_plan(
        self,
        plan_id: int,
    ):
        plan = self.plan_repository.get_by_id(
            plan_id
        )

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        if plan.status != PlanStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign an inactive plan",
            )

        return plan

    def create(
        self,
        data: SIMCreate,
    ) -> SIM:

        existing = self.repository.get_by_number(
            data.sim_number
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="SIM number already exists",
            )

        if data.customer_id is not None:
            self._validate_customer(
                data.customer_id
            )

        if data.plan_id is not None:
            self._validate_plan(
                data.plan_id
            )

        customer_id = data.customer_id
        plan_id = data.plan_id

        if customer_id is not None:
            sim_status = SIMStatus.ACTIVE
            activation_date = date.today()
        else:
            sim_status = SIMStatus.AVAILABLE
            activation_date = None

        sim = SIM(
            sim_number=data.sim_number,
            sim_type=data.sim_type,
            status=sim_status,
            activation_date=activation_date,
            customer_id=customer_id,
            plan_id=plan_id,
            tower_id=data.tower_id, 
        )

        return self.repository.create(sim)

    def get(
        self,
        sim_id: int,
    ) -> SIM:

        sim = self.repository.get_by_id(
            sim_id
        )

        if not sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIM not found",
            )

        return sim

    def update(
        self,
        sim_id: int,
        data: SIMUpdate,
    ) -> SIM:

        sim = self.get(sim_id)

        update_data = data.model_dump(
            exclude_unset=True
        )

        if not update_data:
            return sim

        if "sim_number" in update_data:
            existing = self.repository.get_by_number(
                update_data["sim_number"]
            )

            if (
                existing
                and existing.id != sim.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="SIM number already exists",
                )

        if "customer_id" in update_data:
            customer_id = update_data[
                "customer_id"
            ]

            if customer_id is not None:
                self._validate_customer(
                    customer_id
                )

        if "plan_id" in update_data:
            plan_id = update_data[
                "plan_id"
            ]

            if plan_id is not None:
                self._validate_plan(
                    plan_id
                )

        for field, value in update_data.items():
            setattr(
                sim,
                field,
                value,
            )

        if (
            "customer_id" in update_data
            and update_data["customer_id"] is not None
            and sim.status
            == SIMStatus.AVAILABLE
        ):
            sim.status = SIMStatus.ACTIVE
            sim.activation_date = date.today()

        return self.repository.update(sim)

    def activate(
        self,
        sim_id: int,
    ) -> SIM:

        sim = self.get(sim_id)

        if sim.customer_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "SIM must be assigned to a customer "
                    "before activation"
                ),
            )

        if sim.plan_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "SIM must be assigned to a plan "
                    "before activation"
                ),
            )

        self._validate_customer(
            sim.customer_id
        )

        self._validate_plan(
            sim.plan_id
        )

        sim.status = SIMStatus.ACTIVE
        sim.activation_date = date.today()

        return self.repository.update(sim)

    def suspend(
        self,
        sim_id: int,
    ) -> SIM:

        sim = self.get(sim_id)

        if sim.status == SIMStatus.DEACTIVATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deactivated SIM cannot be suspended",
            )

        sim.status = SIMStatus.SUSPENDED

        return self.repository.update(sim)

    def mark_lost(
        self,
        sim_id: int,
    ) -> SIM:

        sim = self.get(sim_id)

        if sim.status == SIMStatus.DEACTIVATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deactivated SIM cannot be marked as lost",
            )

        sim.status = SIMStatus.LOST

        return self.repository.update(sim)

    def block(
        self,
        sim_id: int,
    ) -> SIM:

        sim = self.get(sim_id)

        if sim.status == SIMStatus.DEACTIVATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deactivated SIM cannot be blocked",
            )

        sim.status = SIMStatus.BLOCKED

        return self.repository.update(sim)

    def deactivate(
        self,
        sim_id: int,
    ) -> SIM:

        sim = self.get(sim_id)

        sim.status = SIMStatus.DEACTIVATED

        return self.repository.update(sim)

    def list(
        self,
        search: str | None = None,
        sim_type=None,
        status=None,
        customer_id: int | None = None,
        plan_id: int | None = None,
    ) -> List[SIM]:

        return self.repository.list(
            search=search,
            sim_type=sim_type,
            status=status,
            customer_id=customer_id,
            plan_id=plan_id,
        )

    def replace(
        self,
        sim_id: int,
        data: SIMReplaceRequest,
        replaced_by: int,
    ) -> SIM:

        old_sim = self.get(sim_id)

        new_sim = self.get(
            data.new_sim_id
        )

        if old_sim.id == new_sim.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old and new SIM cannot be the same",
            )

        if old_sim.customer_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Old SIM is not assigned "
                    "to a customer"
                ),
            )

        if old_sim.status in {
            SIMStatus.DEACTIVATED,
            SIMStatus.BLOCKED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "This SIM cannot be replaced"
                ),
            )

        if new_sim.status != SIMStatus.AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "New SIM must be available"
                ),
            )

        if new_sim.customer_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "New SIM is already assigned "
                    "to a customer"
                ),
            )

        customer_id = old_sim.customer_id
        plan_id = old_sim.plan_id

        new_sim.customer_id = customer_id
        new_sim.plan_id = plan_id
        new_sim.status = SIMStatus.ACTIVE
        new_sim.activation_date = date.today()

        old_sim.status = SIMStatus.DEACTIVATED

        self.db.commit()

        self.db.refresh(
            old_sim
        )

        self.db.refresh(
            new_sim
        )

        self.history_repository.create(
            old_sim_id=old_sim.id,
            new_sim_id=new_sim.id,
            customer_id=customer_id,
            reason=data.reason,
            replaced_by=replaced_by,
        )

        return new_sim

    def replacement_history(
        self,
        sim_id: int,
    ):

        self.get(sim_id)

        return self.history_repository.get_by_sim_id(
            sim_id
        )