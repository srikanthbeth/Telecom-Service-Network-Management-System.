from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.customer import Customer
from models.network_outage import NetworkOutage
from models.plan import Plan
from models.service_request import ServiceRequest
from models.sim import SIM
from models.sla_rule import SLARule
from models.subscription import Subscription
from models.support_ticket import SupportTicket
from models.technician import Technician
from models.technician_assignment import TechnicianAssignment
from models.ticket_sla import TicketSLA
from models.tower import Tower
from models.usage import Usage

from utils.enums import (
    PlanStatus,
    ServiceRequestStatus,
    SIMStatus,
    SubscriptionStatus,
    TechnicianJobStatus,
    TicketStatus,
    TowerStatus,
    UsageType,
)


class DashboardRepository:

    # ========================================================
    # CUSTOMERS
    # ========================================================

    def get_total_customers(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(Customer.id)
        )

        return db.scalar(statement) or 0

    def get_active_customers(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(Customer.id)
        ).where(
            Customer.is_active.is_(True)
        )

        return db.scalar(statement) or 0

    # ========================================================
    # SUBSCRIPTIONS
    # ========================================================

    def get_active_subscriptions(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(Subscription.id)
        ).where(
            Subscription.status
            == SubscriptionStatus.ACTIVE
        )

        return db.scalar(statement) or 0

    # ========================================================
    # SIMS
    # ========================================================

    def get_active_sims(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(SIM.id)
        ).where(
            SIM.status == SIMStatus.ACTIVE
        )

        return db.scalar(statement) or 0

    # ========================================================
    # DATA USAGE
    # ========================================================

    def get_total_data_usage(
        self,
        db: Session,
    ) -> float:
        statement = select(
            func.coalesce(
                func.sum(Usage.quantity),
                0,
            )
        ).where(
            Usage.usage_type == UsageType.DATA
        )

        result = db.scalar(statement)

        return float(result or 0)

    # ========================================================
    # NETWORK OUTAGES
    # ========================================================

    def get_total_outages(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(NetworkOutage.id)
        )

        return db.scalar(statement) or 0

    def get_open_outages(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(NetworkOutage.id)
        ).where(
            NetworkOutage.actual_resolution.is_(None)
        )

        return db.scalar(statement) or 0

    # ========================================================
    # SUPPORT TICKETS
    # ========================================================

    def get_open_tickets(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(SupportTicket.id)
        ).where(
            SupportTicket.status.notin_(
                [
                    TicketStatus.RESOLVED,
                    TicketStatus.CLOSED,
                ]
            )
        )

        return db.scalar(statement) or 0

    # ========================================================
    # SLA
    # ========================================================

    def get_total_sla_records(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(TicketSLA.id)
        )

        return db.scalar(statement) or 0

    def get_breached_slas(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(TicketSLA.id)
        ).where(
            TicketSLA.is_breached.is_(True)
        )

        return db.scalar(statement) or 0

    # ========================================================
    # TECHNICIAN WORKLOAD
    # ========================================================

    def get_technician_workload(
        self,
        db: Session,
    ):
        statement = (
            select(
                Technician.id,
                Technician.full_name,
                func.count(
                    TechnicianAssignment.id
                ).label("total_assignments"),
                func.count(
                    TechnicianAssignment.id
                ).filter(
                    TechnicianAssignment.status.in_(
                        [
                            TechnicianJobStatus.ASSIGNED.value,
                            TechnicianJobStatus.IN_PROGRESS.value,
                        ]
                    )
                ).label("active_assignments"),
                func.count(
                    TechnicianAssignment.id
                ).filter(
                    TechnicianAssignment.status
                    == TechnicianJobStatus.COMPLETED.value
                ).label("completed_assignments"),
            )
            .outerjoin(
                TechnicianAssignment,
                TechnicianAssignment.technician_id
                == Technician.id,
            )
            .group_by(
                Technician.id,
                Technician.full_name,
            )
            .order_by(
                Technician.id
            )
        )

        rows = db.execute(statement).all()

        return [
            {
                "technician_id": row.id,
                "technician_name": row.full_name,
                "total_assignments": (
                    row.total_assignments or 0
                ),
                "active_assignments": (
                    row.active_assignments or 0
                ),
                "completed_assignments": (
                    row.completed_assignments or 0
                ),
            }
            for row in rows
        ]

    # ========================================================
    # TOWERS
    # ========================================================

    def get_total_towers(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(Tower.id)
        )

        return db.scalar(statement) or 0

    def get_active_towers(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(Tower.id)
        ).where(
            Tower.status
            == TowerStatus.ACTIVE.value
        )

        return db.scalar(statement) or 0

    def get_maintenance_towers(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(Tower.id)
        ).where(
            Tower.status
            == TowerStatus.MAINTENANCE.value
        )

        return db.scalar(statement) or 0

    def get_offline_towers(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(Tower.id)
        ).where(
            Tower.status
            == TowerStatus.OFFLINE.value
        )

        return db.scalar(statement) or 0

    def get_decommissioned_towers(
        self,
        db: Session,
    ) -> int:
        statement = select(
            func.count(Tower.id)
        ).where(
            Tower.status
            == TowerStatus.DECOMMISSIONED.value
        )

        return db.scalar(statement) or 0

    # ========================================================
    # SERVICE REQUESTS
    # ========================================================

    def get_service_request_counts(
        self,
        db: Session,
    ):
        total_statement = select(
            func.count(ServiceRequest.id)
        )

        total = db.scalar(
            total_statement
        ) or 0

        pending_statement = select(
            func.count(ServiceRequest.id)
        ).where(
            ServiceRequest.status
            == ServiceRequestStatus.PENDING
        )

        pending = db.scalar(
            pending_statement
        ) or 0

        in_progress_statement = select(
            func.count(ServiceRequest.id)
        ).where(
            ServiceRequest.status
            == ServiceRequestStatus.IN_PROGRESS
        )

        in_progress = db.scalar(
            in_progress_statement
        ) or 0

        approved_statement = select(
            func.count(ServiceRequest.id)
        ).where(
            ServiceRequest.status
            == ServiceRequestStatus.APPROVED
        )

        approved = db.scalar(
            approved_statement
        ) or 0

        rejected_statement = select(
            func.count(ServiceRequest.id)
        ).where(
            ServiceRequest.status
            == ServiceRequestStatus.REJECTED
        )

        rejected = db.scalar(
            rejected_statement
        ) or 0

        completed_statement = select(
            func.count(ServiceRequest.id)
        ).where(
            ServiceRequest.status
            == ServiceRequestStatus.COMPLETED
        )

        completed = db.scalar(
            completed_statement
        ) or 0

        cancelled_statement = select(
            func.count(ServiceRequest.id)
        ).where(
            ServiceRequest.status
            == ServiceRequestStatus.CANCELLED
        )

        cancelled = db.scalar(
            cancelled_statement
        ) or 0

        return {
            "total_service_requests": total,
            "pending_requests": pending,
            "in_progress_requests": in_progress,
            "approved_requests": approved,
            "rejected_requests": rejected,
            "completed_requests": completed,
            "cancelled_requests": cancelled,
        }

    # ========================================================
    # PLAN UTILIZATION
    # ========================================================

    def get_plan_utilization(
        self,
        db: Session,
    ):
        statement = (
            select(
                Plan.id,
                Plan.plan_name,
                Plan.data_limit_mb,
                func.count(
                    Subscription.id
                ).label(
                    "active_subscriptions"
                ),
            )
            .outerjoin(
                Subscription,
                (
                    Subscription.plan_id
                    == Plan.id
                )
                & (
                    Subscription.status
                    == SubscriptionStatus.ACTIVE
                ),
            )
            .where(
                Plan.status == PlanStatus.ACTIVE
            )
            .group_by(
                Plan.id,
                Plan.plan_name,
                Plan.data_limit_mb,
            )
            .order_by(
                Plan.id
            )
        )

        rows = db.execute(statement).all()

        return [
            {
                "plan_id": row.id,
                "plan_name": row.plan_name,
                "active_subscriptions": (
                    row.active_subscriptions or 0
                ),
                "data_limit_mb": (
                    row.data_limit_mb or 0
                ),
            }
            for row in rows
        ]