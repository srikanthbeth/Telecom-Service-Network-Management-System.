from calendar import monthrange
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.usage import Usage
from repositories.customer_repository import CustomerRepository
from repositories.plan_repository import PlanRepository
from repositories.sim_repository import SIMRepository
from repositories.subscription_repository import SubscriptionRepository
from repositories.usage_repository import UsageRepository
from schemas.usage import (
    UsageCreate,
    UsageSummaryResponse,
    UsageUtilizationResponse,
)
from utils.enums import (
    AccountStatus,
    SIMStatus,
    SubscriptionStatus,
    UsageType,
)


class UsageService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.repository = UsageRepository()
        self.customer_repository = CustomerRepository(db)
        self.sim_repository = SIMRepository(db)
        self.subscription_repository = SubscriptionRepository()
        self.plan_repository = PlanRepository(db)

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate_customer(
    self,
    customer_id: int,
):
     customer = self.customer_repository.get_by_id(
        customer_id
    )

     if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

     return customer

    def _validate_sim(
        self,
        sim_id: int,
        customer_id: int,
    ):

        sim = self.sim_repository.get_by_id(
            sim_id
        )

        if not sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIM not found",
            )

        if sim.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SIM and customer must match",
            )

        if sim.status != SIMStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SIM must be active",
            )

        return sim

    def _validate_subscription(
        self,
        subscription_id: int,
        customer_id: int,
        sim_id: int,
    ):

        subscription = self.subscription_repository.get_by_id(
            self.db,
            subscription_id,
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        if subscription.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription and customer must match",
            )

        if subscription.sim_id != sim_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription and SIM must match",
            )

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription must be active",
            )

        return subscription

    # =====================================================
    # CREATE USAGE
    # =====================================================

    def create(
        self,
        data: UsageCreate,
    ):

        self._validate_customer(
            data.customer_id
        )

        self._validate_sim(
            data.sim_id,
            data.customer_id,
        )

        subscription = self._validate_subscription(
            data.subscription_id,
            data.customer_id,
            data.sim_id,
        )

        if not (
            subscription.start_date
            <= data.usage_date
            <= subscription.end_date
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usage date must be within subscription period",
            )

        usage = Usage(
            customer_id=data.customer_id,
            sim_id=data.sim_id,
            subscription_id=data.subscription_id,
            usage_type=data.usage_type,
            usage_date=data.usage_date,
            quantity=data.quantity,
        )

        usage = self.repository.create(
            self.db,
            usage,
        )

        self.db.commit()
        self.db.refresh(usage)

        return usage

    # =====================================================
    # GET
    # =====================================================

    def get(
        self,
        usage_id: int,
    ):

        usage = self.repository.get_by_id(
            self.db,
            usage_id,
        )

        if not usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usage record not found",
            )

        return usage

    # =====================================================
    # LIST
    # =====================================================

    def list(
        self,
        customer_id=None,
        sim_id=None,
        subscription_id=None,
        usage_type=None,
        usage_date=None,
    ):

        return self.repository.list(
            self.db,
            customer_id=customer_id,
            sim_id=sim_id,
            subscription_id=subscription_id,
            usage_type=usage_type,
            usage_date=usage_date,
        )

    # =====================================================
    # CUSTOMER USAGE
    # =====================================================

    def customer_usage(
        self,
        customer_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ):

        self._validate_customer(
            customer_id
        )

        data_usage = self.repository.get_customer_total(
            self.db,
            customer_id,
            UsageType.DATA,
            start_date,
            end_date,
        )

        voice_usage = self.repository.get_customer_total(
            self.db,
            customer_id,
            UsageType.VOICE,
            start_date,
            end_date,
        )

        sms_usage = self.repository.get_customer_total(
            self.db,
            customer_id,
            UsageType.SMS,
            start_date,
            end_date,
        )

        return {
            "customer_id": customer_id,
            "sim_id": 0,
            "subscription_id": 0,
            "data_usage_mb": data_usage,
            "voice_usage_minutes": voice_usage,
            "sms_usage": sms_usage,
            "total_records": 0,
        }

    # =====================================================
    # SIM USAGE
    # =====================================================

    def sim_usage(
        self,
        sim_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ):

        sim = self.sim_repository.get_by_id(
            sim_id
        )

        if not sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIM not found",
            )

        data_usage = self.repository.get_sim_total(
            self.db,
            sim_id,
            UsageType.DATA,
            start_date,
            end_date,
        )

        voice_usage = self.repository.get_sim_total(
            self.db,
            sim_id,
            UsageType.VOICE,
            start_date,
            end_date,
        )

        sms_usage = self.repository.get_sim_total(
            self.db,
            sim_id,
            UsageType.SMS,
            start_date,
            end_date,
        )

        total_records = self.repository.count_sim_records(
            self.db,
            sim_id,
            start_date,
            end_date,
        )

        subscription_id = 0

        active_subscription = (
            self.subscription_repository.get_active_by_sim(
                self.db,
                sim_id,
            )
        )

        if active_subscription:
            subscription_id = active_subscription.id

        return {
            "customer_id": sim.customer_id or 0,
            "sim_id": sim_id,
            "subscription_id": subscription_id,
            "data_usage_mb": data_usage,
            "voice_usage_minutes": voice_usage,
            "sms_usage": sms_usage,
            "total_records": total_records,
        }

    # =====================================================
    # DAILY USAGE
    # =====================================================

    def daily_usage(
        self,
        sim_id: int,
        usage_date: date,
    ):

        return self.sim_usage(
            sim_id,
            usage_date,
            usage_date,
        )

    # =====================================================
    # MONTHLY USAGE
    # =====================================================

    def monthly_usage(
        self,
        sim_id: int,
        year: int,
        month: int,
    ):

        if month < 1 or month > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Month must be between 1 and 12",
            )

        start_date = date(
            year,
            month,
            1,
        )

        last_day = monthrange(
            year,
            month,
        )[1]

        end_date = date(
            year,
            month,
            last_day,
        )

        return self.sim_usage(
            sim_id,
            start_date,
            end_date,
        )

    # =====================================================
    # PLAN UTILIZATION
    # =====================================================

    def plan_utilization(
        self,
        sim_id: int,
    ):

        sim = self.sim_repository.get_by_id(
            sim_id
        )

        if not sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIM not found",
            )

        subscription = (
            self.subscription_repository.get_active_by_sim(
                self.db,
                sim_id,
            )
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active subscription not found",
            )

        plan = self.plan_repository.get_by_id(
            subscription.plan_id
        )

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        data_used = self.repository.get_sim_total(
            self.db,
            sim_id,
            UsageType.DATA,
            subscription.start_date,
            subscription.end_date,
        )

        voice_used = self.repository.get_sim_total(
            self.db,
            sim_id,
            UsageType.VOICE,
            subscription.start_date,
            subscription.end_date,
        )

        sms_used = self.repository.get_sim_total(
            self.db,
            sim_id,
            UsageType.SMS,
            subscription.start_date,
            subscription.end_date,
        )

        data_limit = float(
            plan.data_limit_mb
        )

        voice_limit = float(
            plan.voice_limit_minutes
        )

        sms_limit = float(
            plan.sms_limit
        )

        data_percentage = self._percentage(
            data_used,
            data_limit,
        )

        voice_percentage = self._percentage(
            voice_used,
            voice_limit,
        )

        sms_percentage = self._percentage(
            sms_used,
            sms_limit,
        )

        return UsageUtilizationResponse(
            customer_id=subscription.customer_id,
            sim_id=subscription.sim_id,
            subscription_id=subscription.id,
            plan_id=plan.id,

            data_used_mb=data_used,
            data_limit_mb=data_limit,
            data_percentage=data_percentage,
            data_remaining_mb=max(
                data_limit - data_used,
                0,
            ),

            voice_used_minutes=voice_used,
            voice_limit_minutes=voice_limit,
            voice_percentage=voice_percentage,
            voice_remaining_minutes=max(
                voice_limit - voice_used,
                0,
            ),

            sms_used=sms_used,
            sms_limit=sms_limit,
            sms_percentage=sms_percentage,
            sms_remaining=max(
                sms_limit - sms_used,
                0,
            ),
        )

    # =====================================================
    # PERCENTAGE
    # =====================================================

    @staticmethod
    def _percentage(
        used: float,
        limit: float,
    ) -> float:

        if limit <= 0:
            return 0.0

        percentage = (
            used / limit
        ) * 100

        return round(
            min(percentage, 100),
            2,
        )