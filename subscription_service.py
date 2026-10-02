from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.subscription import Subscription
from models.subscription_history import SubscriptionHistory

from repositories.customer_repository import CustomerRepository
from repositories.sim_repository import SIMRepository
from repositories.subscription_history_repository import (
    SubscriptionHistoryRepository,
)
from repositories.subscription_repository import (
    SubscriptionRepository,
)

from utils.enums import (
    SIMStatus,
    SubscriptionStatus,
)


class SubscriptionService:

    def __init__(self):
        self.subscription_repository = (
            SubscriptionRepository()
        )

        self.history_repository = (
            SubscriptionHistoryRepository()
        )

    # =========================================================
    # GET SUBSCRIPTION
    # =========================================================

    def _get_subscription(
        self,
        db: Session,
        subscription_id: int,
    ) -> Subscription:

        subscription = (
            self.subscription_repository.get_by_id(
                db,
                subscription_id,
            )
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        return subscription

    # =========================================================
    # VALIDATE CUSTOMER
    # =========================================================

    def _validate_customer(
        self,
        db: Session,
        customer_id: int,
    ):

        repository = CustomerRepository(db)

        customer = repository.get_by_id(
            customer_id,
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer is inactive",
            )

        return customer

    # =========================================================
    # VALIDATE SIM
    # =========================================================

    def _validate_sim(
        self,
        db: Session,
        sim_id: int,
        customer_id: int,
    ):

        repository = SIMRepository(db)

        sim = repository.get_by_id(
            sim_id,
        )

        if not sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIM not found",
            )

        if sim.status != SIMStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active SIMs can have a subscription",
            )

        if sim.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SIM and customer must match",
            )

        return sim

    # =========================================================
    # VALIDATE PLAN
    # =========================================================

    def _validate_plan(
        self,
        db: Session,
        plan_id: int,
    ):

        from repositories.plan_repository import PlanRepository
        from utils.enums import PlanStatus
        
        repository = PlanRepository(db)

        plan = repository.get_by_id(
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
                detail="Plan is inactive",
            )

        return plan

    # =========================================================
    # HISTORY
    # =========================================================

    def _create_history(
        self,
        db: Session,
        subscription: Subscription,
        action: str,
        previous_plan_id: int | None = None,
        new_plan_id: int | None = None,
        previous_status: str | None = None,
        new_status: str | None = None,
        description: str | None = None,
        changed_by: int | None = None,
    ):

        history = SubscriptionHistory(
            subscription_id=subscription.id,
            action=action,
            previous_plan_id=previous_plan_id,
            new_plan_id=new_plan_id,
            previous_status=previous_status,
            new_status=new_status,
            description=description,
            changed_by=changed_by,
        )

        return self.history_repository.create(
            db,
            history,
        )

    # =========================================================
    # CREATE SUBSCRIPTION
    # =========================================================

    def create(
        self,
        db: Session,
        customer_id: int,
        sim_id: int,
        plan_id: int,
        start_date: date,
        end_date: date,
        changed_by: int | None = None,
    ) -> Subscription:

        if end_date <= start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date",
            )

        self._validate_customer(
            db,
            customer_id,
        )

        self._validate_sim(
            db,
            sim_id,
            customer_id,
        )

        self._validate_plan(
            db,
            plan_id,
        )

        existing = (
            self.subscription_repository.get_active_by_sim(
                db,
                sim_id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="SIM already has an active subscription",
            )

        subscription = Subscription(
            customer_id=customer_id,
            sim_id=sim_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            status=SubscriptionStatus.ACTIVE,
        )

        subscription = (
            self.subscription_repository.create(
                db,
                subscription,
            )
        )

        self._create_history(
            db=db,
            subscription=subscription,
            action="Created",
            new_plan_id=plan_id,
            new_status=SubscriptionStatus.ACTIVE.value,
            description="Subscription created",
            changed_by=changed_by,
        )

        db.commit()
        db.refresh(subscription)

        return subscription

    # =========================================================
    # GET
    # =========================================================

    def get(
        self,
        db: Session,
        subscription_id: int,
    ) -> Subscription:

        return self._get_subscription(
            db,
            subscription_id,
        )

    # =========================================================
    # LIST
    # =========================================================

    def list(
        self,
        db: Session,
        customer_id: int | None = None,
        sim_id: int | None = None,
        plan_id: int | None = None,
        status: SubscriptionStatus | None = None,
    ):

        return self.subscription_repository.list(
            db=db,
            customer_id=customer_id,
            sim_id=sim_id,
            plan_id=plan_id,
            status=status,
        )

    # =========================================================
    # UPGRADE
    # =========================================================

    def upgrade(
        self,
        db: Session,
        subscription_id: int,
        plan_id: int,
        changed_by: int | None = None,
    ) -> Subscription:

        subscription = self._get_subscription(
            db,
            subscription_id,
        )

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active subscriptions can change plans",
            )

        self._validate_plan(
            db,
            plan_id,
        )

        if subscription.plan_id == plan_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription is already on this plan",
            )

        previous_plan_id = subscription.plan_id

        subscription.plan_id = plan_id

        self.subscription_repository.update(
            db,
            subscription,
        )

        self._create_history(
            db=db,
            subscription=subscription,
            action="Plan Upgrade",
            previous_plan_id=previous_plan_id,
            new_plan_id=plan_id,
            previous_status=subscription.status.value,
            new_status=subscription.status.value,
            description="Subscription plan upgraded",
            changed_by=changed_by,
        )

        db.commit()
        db.refresh(subscription)

        return subscription

    # =========================================================
    # DOWNGRADE
    # =========================================================

    def downgrade(
        self,
        db: Session,
        subscription_id: int,
        plan_id: int,
        changed_by: int | None = None,
    ) -> Subscription:

        subscription = self._get_subscription(
            db,
            subscription_id,
        )

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active subscriptions can change plans",
            )

        self._validate_plan(
            db,
            plan_id,
        )

        if subscription.plan_id == plan_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription is already on this plan",
            )

        previous_plan_id = subscription.plan_id

        subscription.plan_id = plan_id

        self.subscription_repository.update(
            db,
            subscription,
        )

        self._create_history(
            db=db,
            subscription=subscription,
            action="Plan Downgrade",
            previous_plan_id=previous_plan_id,
            new_plan_id=plan_id,
            previous_status=subscription.status.value,
            new_status=subscription.status.value,
            description="Subscription plan downgraded",
            changed_by=changed_by,
        )

        db.commit()
        db.refresh(subscription)

        return subscription

    # =========================================================
    # RENEW
    # =========================================================

    def renew(
        self,
        db: Session,
        subscription_id: int,
        end_date: date,
        changed_by: int | None = None,
    ) -> Subscription:

        subscription = self._get_subscription(
            db,
            subscription_id,
        )

        if subscription.status in (
            SubscriptionStatus.CANCELLED,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cancelled subscriptions cannot be renewed",
            )

        if end_date <= subscription.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Renewal end date must be after current end date",
            )

        previous_end_date = subscription.end_date

        subscription.end_date = end_date

        if subscription.status == SubscriptionStatus.EXPIRED:
            subscription.status = SubscriptionStatus.ACTIVE

        self.subscription_repository.update(
            db,
            subscription,
        )

        self._create_history(
            db=db,
            subscription=subscription,
            action="Renewed",
            previous_plan_id=subscription.plan_id,
            new_plan_id=subscription.plan_id,
            previous_status=SubscriptionStatus.EXPIRED.value,
            new_status=subscription.status.value,
            description=(
                f"Subscription renewed from "
                f"{previous_end_date} to {end_date}"
            ),
            changed_by=changed_by,
        )

        db.commit()
        db.refresh(subscription)

        return subscription

    # =========================================================
    # SUSPEND
    # =========================================================

    def suspend(
        self,
        db: Session,
        subscription_id: int,
        changed_by: int | None = None,
    ) -> Subscription:

        subscription = self._get_subscription(
            db,
            subscription_id,
        )

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active subscriptions can be suspended",
            )

        previous_status = subscription.status.value

        subscription.status = SubscriptionStatus.SUSPENDED

        self.subscription_repository.update(
            db,
            subscription,
        )

        self._create_history(
            db=db,
            subscription=subscription,
            action="Suspended",
            previous_plan_id=subscription.plan_id,
            new_plan_id=subscription.plan_id,
            previous_status=previous_status,
            new_status=subscription.status.value,
            description="Subscription suspended",
            changed_by=changed_by,
        )

        db.commit()
        db.refresh(subscription)

        return subscription

    # =========================================================
    # REACTIVATE
    # =========================================================

    def reactivate(
        self,
        db: Session,
        subscription_id: int,
        changed_by: int | None = None,
    ) -> Subscription:

        subscription = self._get_subscription(
            db,
            subscription_id,
        )

        if subscription.status != SubscriptionStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only suspended subscriptions can be reactivated",
            )

        previous_status = subscription.status.value

        subscription.status = SubscriptionStatus.ACTIVE

        self.subscription_repository.update(
            db,
            subscription,
        )

        self._create_history(
            db=db,
            subscription=subscription,
            action="Reactivated",
            previous_plan_id=subscription.plan_id,
            new_plan_id=subscription.plan_id,
            previous_status=previous_status,
            new_status=subscription.status.value,
            description="Subscription reactivated",
            changed_by=changed_by,
        )

        db.commit()
        db.refresh(subscription)

        return subscription

    # =========================================================
    # CANCEL
    # =========================================================

    def cancel(
        self,
        db: Session,
        subscription_id: int,
        changed_by: int | None = None,
    ) -> Subscription:

        subscription = self._get_subscription(
            db,
            subscription_id,
        )

        if subscription.status == SubscriptionStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription is already cancelled",
            )

        previous_status = subscription.status.value

        subscription.status = SubscriptionStatus.CANCELLED

        self.subscription_repository.update(
            db,
            subscription,
        )

        self._create_history(
            db=db,
            subscription=subscription,
            action="Cancelled",
            previous_plan_id=subscription.plan_id,
            new_plan_id=subscription.plan_id,
            previous_status=previous_status,
            new_status=subscription.status.value,
            description="Subscription cancelled",
            changed_by=changed_by,
        )

        db.commit()
        db.refresh(subscription)

        return subscription

    # =========================================================
    # HISTORY
    # =========================================================

    def history(
        self,
        db: Session,
        subscription_id: int,
    ):

        self._get_subscription(
            db,
            subscription_id,
        )

        return self.history_repository.get_by_subscription_id(
            db,
            subscription_id,
        )