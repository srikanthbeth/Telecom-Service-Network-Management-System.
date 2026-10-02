from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.plan import Plan
from repositories.plan_repository import PlanRepository
from schemas.plan import PlanCreate, PlanUpdate
from utils.enums import PlanStatus, PlanType


class PlanService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = PlanRepository(db)

    def create(
        self,
        data: PlanCreate,
    ) -> Plan:

        existing = self.repository.get_by_name(
            data.plan_name
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Plan name already exists",
            )

        plan = Plan(
            plan_name=data.plan_name,
            description=data.description,
            plan_type=data.plan_type,
            validity_days=data.validity_days,
            data_limit_mb=data.data_limit_mb,
            voice_limit_minutes=data.voice_limit_minutes,
            sms_limit=data.sms_limit,
            price=data.price,
            status=PlanStatus.ACTIVE,
        )

        return self.repository.create(plan)

    def get(
        self,
        plan_id: int,
    ) -> Plan:

        plan = self.repository.get_by_id(
            plan_id
        )

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        return plan

    def update(
        self,
        plan_id: int,
        data: PlanUpdate,
    ) -> Plan:

        plan = self.get(plan_id)

        update_data = data.model_dump(
            exclude_unset=True
        )

        if not update_data:
            return plan

        if "plan_name" in update_data:
            existing = self.repository.get_by_name(
                update_data["plan_name"]
            )

            if (
                existing
                and existing.id != plan.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Plan name already exists",
                )

        for field, value in update_data.items():
            setattr(
                plan,
                field,
                value,
            )

        return self.repository.update(plan)

    def activate(
        self,
        plan_id: int,
    ) -> Plan:

        plan = self.get(plan_id)

        plan.status = PlanStatus.ACTIVE

        return self.repository.update(plan)

    def deactivate(
        self,
        plan_id: int,
    ) -> Plan:

        plan = self.get(plan_id)

        plan.status = PlanStatus.INACTIVE

        return self.repository.update(plan)

    def list(
        self,
        search: str | None = None,
        plan_type: PlanType | None = None,
        status: PlanStatus | None = None,
    ) -> List[Plan]:

        return self.repository.list(
            search=search,
            plan_type=plan_type,
            status=status,
        )

    def compare(
        self,
        plan_ids: List[int],
    ) -> List[Plan]:

        if len(plan_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "At least two plan IDs "
                    "are required for comparison"
                ),
            )

        if len(plan_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A maximum of five plans "
                    "can be compared"
                ),
            )

        if len(set(plan_ids)) != len(plan_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Duplicate plan IDs "
                    "are not allowed"
                ),
            )

        plans = self.repository.get_by_ids(
            plan_ids
        )

        if len(plans) != len(plan_ids):
            found_ids = {
                plan.id
                for plan in plans
            }

            missing_ids = [
                plan_id
                for plan_id in plan_ids
                if plan_id not in found_ids
            ]

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Plans not found: {missing_ids}"
                ),
            )

        plan_map = {
            plan.id: plan
            for plan in plans
        }

        return [
            plan_map[plan_id]
            for plan_id in plan_ids
        ]