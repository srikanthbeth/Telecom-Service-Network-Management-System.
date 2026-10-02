from datetime import date, datetime, time, timezone

from sqlalchemy import Integer, func, select
from sqlalchemy.orm import Session

from models.customer import Customer
from models.network_outage import NetworkOutage
from models.plan import Plan
from models.service_request import ServiceRequest
from models.subscription import Subscription
from models.support_ticket import SupportTicket
from models.technician import Technician
from models.technician_assignment import TechnicianAssignment
from models.ticket_sla import TicketSLA
from models.usage import Usage

from utils.enums import (
    ServiceRequestStatus,
    SubscriptionStatus,
    TechnicianJobStatus,
    TicketStatus,
    UsageType,
)


class ReportsRepository:

    def _date_filter(
        self,
        column,
        start_date: date | None,
        end_date: date | None,
    ):
        conditions = []

        if start_date:
            conditions.append(column >= start_date)

        if end_date:
            conditions.append(column <= end_date)

        return conditions

    def _paginate(
        self,
        statement,
        db: Session,
        page: int,
        page_size: int,
    ):
        total_statement = select(func.count()).select_from(
            statement.order_by(None).subquery()
        )

        total = db.scalar(total_statement) or 0

        offset = (page - 1) * page_size

        rows = db.execute(
            statement.offset(offset).limit(page_size)
        ).all()

        total_pages = (
            (total + page_size - 1) // page_size
            if total
            else 0
        )

        return rows, total, total_pages

    # ---------------------------------------------------------
    # CUSTOMER GROWTH
    # ---------------------------------------------------------

    def customer_growth(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        location=None,
        status=None,
        search=None,
        page=1,
        page_size=20,
        sort_order="desc",
    ):
        conditions = self._date_filter(
            Customer.created_at,
            start_date,
            end_date,
        )

        if location:
            location_value = f"%{location}%"

            conditions.append(
                Customer.city.ilike(location_value)
                | Customer.state.ilike(location_value)
                | Customer.country.ilike(location_value)
            )

        if status:
            if status.lower() == "active":
                conditions.append(
                    Customer.is_active.is_(True)
                )
            elif status.lower() == "inactive":
                conditions.append(
                    Customer.is_active.is_(False)
                )

        if search:
            conditions.append(
                Customer.customer_number.ilike(
                    f"%{search}%"
                )
            )

        filtered = (
            select(Customer)
            .where(*conditions)
            .subquery()
        )

        statement = (
            select(
                func.date(
                    filtered.c.created_at
                ).label("date"),
                func.count(
                    filtered.c.id
                ).label("count"),
            )
            .group_by(
                func.date(
                    filtered.c.created_at
                )
            )
        )

        if sort_order.lower() == "asc":
            statement = statement.order_by(
                func.date(
                    filtered.c.created_at
                ).asc()
            )
        else:
            statement = statement.order_by(
                func.date(
                    filtered.c.created_at
                ).desc()
            )

        return self._paginate(
            statement,
            db,
            page,
            page_size,
        )

    # ---------------------------------------------------------
    # SUBSCRIPTION TRENDS
    # ---------------------------------------------------------

    def subscription_trends(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        customer_id=None,
        plan_id=None,
        status=None,
        search=None,
        page=1,
        page_size=20,
        sort_order="desc",
    ):
        conditions = self._date_filter(
            Subscription.start_date,
            start_date,
            end_date,
        )

        if customer_id:
            conditions.append(
                Subscription.customer_id == customer_id
            )

        if plan_id:
            conditions.append(
                Subscription.plan_id == plan_id
            )

        if status:
            conditions.append(
                Subscription.status == status
            )

        if search:
            conditions.append(
                Plan.plan_name.ilike(
                    f"%{search}%"
                )
            )

        statement = (
            select(
                Subscription.start_date.label("date"),
                func.count(
                    Subscription.id
                ).label("count"),
            )
            .join(
                Plan,
                Plan.id == Subscription.plan_id,
            )
            .where(*conditions)
            .group_by(
                Subscription.start_date
            )
        )

        if sort_order.lower() == "asc":
            statement = statement.order_by(
                Subscription.start_date.asc()
            )
        else:
            statement = statement.order_by(
                Subscription.start_date.desc()
            )

        return self._paginate(
            statement,
            db,
            page,
            page_size,
        )

    # ---------------------------------------------------------
    # PLAN POPULARITY
    # ---------------------------------------------------------

    def plan_popularity(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        customer_id=None,
        plan_id=None,
        status=None,
        search=None,
        page=1,
        page_size=20,
        sort_order="desc",
    ):
        conditions = [
            Subscription.status
            == SubscriptionStatus.ACTIVE
        ]

        if start_date:
            conditions.append(
                Subscription.start_date >= start_date
            )

        if end_date:
            conditions.append(
                Subscription.start_date <= end_date
            )

        if customer_id:
            conditions.append(
                Subscription.customer_id == customer_id
            )

        if plan_id:
            conditions.append(
                Subscription.plan_id == plan_id
            )

        if status:
            conditions.append(
                Subscription.status == status
            )

        if search:
            conditions.append(
                Plan.plan_name.ilike(
                    f"%{search}%"
                )
            )

        statement = (
            select(
                Plan.id.label("plan_id"),
                Plan.plan_name.label("plan_name"),
                func.count(
                    Subscription.id
                ).label(
                    "subscription_count"
                ),
            )
            .join(
                Subscription,
                Subscription.plan_id == Plan.id,
            )
            .where(*conditions)
            .group_by(
                Plan.id,
                Plan.plan_name,
            )
        )

        if sort_order.lower() == "asc":
            statement = statement.order_by(
                func.count(
                    Subscription.id
                ).asc()
            )
        else:
            statement = statement.order_by(
                func.count(
                    Subscription.id
                ).desc()
            )

        return self._paginate(
            statement,
            db,
            page,
            page_size,
        )

    # ---------------------------------------------------------
    # DATA CONSUMPTION
    # ---------------------------------------------------------

    def data_consumption(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        customer_id=None,
        plan_id=None,
        status=None,
        search=None,
        page=1,
        page_size=20,
        sort_order="desc",
    ):
        conditions = [
            Usage.usage_type == UsageType.DATA
        ]

        if start_date:
            conditions.append(
                Usage.usage_date >= start_date
            )

        if end_date:
            conditions.append(
                Usage.usage_date <= end_date
            )

        if customer_id:
            conditions.append(
                Usage.customer_id == customer_id
            )

        if plan_id:
            conditions.append(
                Subscription.plan_id == plan_id
            )

        if status:
            conditions.append(
                Subscription.status == status
            )

        if search:
            conditions.append(
                Plan.plan_name.ilike(
                    f"%{search}%"
                )
            )

        statement = (
            select(
                Usage.usage_date.label("date"),
                func.coalesce(
                    func.sum(Usage.quantity),
                    0,
                ).label("total_usage"),
            )
            .join(
                Subscription,
                Subscription.id == Usage.subscription_id,
            )
            .join(
                Plan,
                Plan.id == Subscription.plan_id,
            )
            .where(*conditions)
            .group_by(
                Usage.usage_date
            )
        )

        if sort_order.lower() == "asc":
            statement = statement.order_by(
                Usage.usage_date.asc()
            )
        else:
            statement = statement.order_by(
                Usage.usage_date.desc()
            )

        return self._paginate(
            statement,
            db,
            page,
            page_size,
        )

    # ---------------------------------------------------------
    # NETWORK UPTIME
    # ---------------------------------------------------------

    def network_uptime(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        page=1,
        page_size=20,
        sort_order="desc",
    ):
        conditions = []

        if start_date:
            period_start = datetime.combine(
                start_date,
                time.min,
            ).replace(
                tzinfo=timezone.utc
            )

            conditions.append(
                NetworkOutage.start_time >=
                period_start
            )
        else:
            period_start = datetime.now(
                timezone.utc
            )

        if end_date:
            period_end = datetime.combine(
                end_date,
                time.max,
            ).replace(
                tzinfo=timezone.utc
            )

            conditions.append(
                NetworkOutage.start_time <=
                period_end
            )
        else:
            period_end = datetime.now(
                timezone.utc
            )

        statement = (
            select(NetworkOutage)
            .where(*conditions)
        )

        outages = db.scalars(
            statement
        ).all()

        total_minutes = max(
            (
                period_end - period_start
            ).total_seconds() / 60,
            1,
        )

        outage_minutes = 0

        for outage in outages:
            outage_start = outage.start_time

            outage_end = (
                outage.actual_resolution
                or period_end
            )

            start = max(
                outage_start,
                period_start,
            )

            end = min(
                outage_end,
                period_end,
            )

            if end > start:
                outage_minutes += (
                    end - start
                ).total_seconds() / 60

        uptime_percentage = max(
            0,
            (
                (
                    total_minutes
                    - outage_minutes
                )
                / total_minutes
            ) * 100,
        )

        rows = [
            {
                "label": "Network",
                "value": round(
                    uptime_percentage,
                    2,
                ),
            }
        ]

        return (
            rows,
            1,
            1,
        )

    # ---------------------------------------------------------
    # OUTAGE FREQUENCY
    # ---------------------------------------------------------

    def outage_frequency(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        status=None,
        search=None,
        page=1,
        page_size=20,
        sort_order="desc",
    ):
        conditions = []

        if start_date:
            conditions.append(
                NetworkOutage.start_time >=
                datetime.combine(
                    start_date,
                    time.min,
                ).replace(
                    tzinfo=timezone.utc
                )
            )

        if end_date:
            conditions.append(
                NetworkOutage.start_time <=
                datetime.combine(
                    end_date,
                    time.max,
                ).replace(
                    tzinfo=timezone.utc
                )
            )

        if status:
            conditions.append(
                NetworkOutage.severity == status
            )

        if search:
            conditions.append(
                NetworkOutage.outage_type.ilike(
                    f"%{search}%"
                )
            )

        statement = (
            select(
                func.date(
                    NetworkOutage.start_time
                ).label("date"),
                func.count(
                    NetworkOutage.id
                ).label("count"),
            )
            .where(*conditions)
            .group_by(
                func.date(
                    NetworkOutage.start_time
                )
            )
        )

        if sort_order.lower() == "asc":
            statement = statement.order_by(
                func.date(
                    NetworkOutage.start_time
                ).asc()
            )
        else:
            statement = statement.order_by(
                func.date(
                    NetworkOutage.start_time
                ).desc()
            )

        return self._paginate(
            statement,
            db,
            page,
            page_size,
        )

    # ---------------------------------------------------------
    # TICKET RESOLUTION
    # ---------------------------------------------------------

    def ticket_resolution(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        customer_id=None,
        status=None,
        search=None,
        page=1,
        page_size=20,
        sort_order="desc",
    ):
        conditions = [
            SupportTicket.resolved_at.is_not(None)
        ]

        if start_date:
            conditions.append(
                SupportTicket.created_at >=
                datetime.combine(
                    start_date,
                    time.min,
                ).replace(
                    tzinfo=timezone.utc
                )
            )

        if end_date:
            conditions.append(
                SupportTicket.created_at <=
                datetime.combine(
                    end_date,
                    time.max,
                ).replace(
                    tzinfo=timezone.utc
                )
            )

        if customer_id:
            conditions.append(
                SupportTicket.customer_id ==
                customer_id
            )

        if status:
            conditions.append(
                SupportTicket.status == status
            )

        if search:
            conditions.append(
                SupportTicket.subject.ilike(
                    f"%{search}%"
                )
            )

        resolution_minutes = (
            func.extract(
                "epoch",
                SupportTicket.resolved_at
                - SupportTicket.created_at,
            ) / 60
        )

        statement = (
            select(
                func.date(
                    SupportTicket.created_at
                ).label("date"),
                func.avg(
                    resolution_minutes
                ).label(
                    "average_resolution_minutes"
                ),
                func.count(
                    SupportTicket.id
                ).label(
                    "ticket_count"
                ),
            )
            .where(*conditions)
            .group_by(
                func.date(
                    SupportTicket.created_at
                )
            )
        )

        if sort_order.lower() == "asc":
            statement = statement.order_by(
                func.date(
                    SupportTicket.created_at
                ).asc()
            )
        else:
            statement = statement.order_by(
                func.date(
                    SupportTicket.created_at
                ).desc()
            )

        return self._paginate(
            statement,
            db,
            page,
            page_size,
        )

    # ---------------------------------------------------------
    # SLA PERFORMANCE
    # ---------------------------------------------------------

    def sla_performance(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        customer_id=None,
        status=None,
        search=None,
        page=1,
        page_size=20,
        sort_order="desc",
    ):
        conditions = []

        if start_date:
            conditions.append(
                TicketSLA.start_time >=
                datetime.combine(
                    start_date,
                    time.min,
                ).replace(
                    tzinfo=timezone.utc
                )
            )

        if end_date:
            conditions.append(
                TicketSLA.start_time <=
                datetime.combine(
                    end_date,
                    time.max,
                ).replace(
                    tzinfo=timezone.utc
                )
            )

        if customer_id:
            conditions.append(
                SupportTicket.customer_id ==
                customer_id
            )

        if status:
            if status.lower() == "breached":
                conditions.append(
                    TicketSLA.is_breached.is_(True)
                )
            elif status.lower() in (
                "met",
                "resolved",
            ):
                conditions.append(
                    TicketSLA.is_breached.is_(False)
                )

        if search:
            conditions.append(
                SupportTicket.ticket_number.ilike(
                    f"%{search}%"
                )
            )

        statement = (
            select(
                func.date(
                    TicketSLA.start_time
                ).label("date"),
                func.count(
                    TicketSLA.id
                ).label("total_slas"),
                func.sum(
                    func.cast(
                        TicketSLA.is_breached,
                        Integer,
                    )
                ).label(
                    "breached_slas"
                ),
            )
            .join(
                SupportTicket,
                SupportTicket.id ==
                TicketSLA.ticket_id,
            )
            .where(*conditions)
            .group_by(
                func.date(
                    TicketSLA.start_time
                )
            )
        )

        if sort_order.lower() == "asc":
            statement = statement.order_by(
                func.date(
                    TicketSLA.start_time
                ).asc()
            )
        else:
            statement = statement.order_by(
                func.date(
                    TicketSLA.start_time
                ).desc()
            )

        return self._paginate(
            statement,
            db,
            page,
            page_size,
        )

    # ---------------------------------------------------------
    # TECHNICIAN PERFORMANCE
    # ---------------------------------------------------------

    def technician_performance(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        customer_id=None,
        status=None,
        search=None,
        page=1,
        page_size=20,
        sort_order="desc",
    ):
        conditions = []

        if start_date:
            conditions.append(
                TechnicianAssignment.assigned_at >=
                datetime.combine(
                    start_date,
                    time.min,
                ).replace(
                    tzinfo=timezone.utc
                )
            )

        if end_date:
            conditions.append(
                TechnicianAssignment.assigned_at <=
                datetime.combine(
                    end_date,
                    time.max,
                ).replace(
                    tzinfo=timezone.utc
                )
            )

        if customer_id:
            conditions.append(
                TechnicianAssignment.customer_id ==
                customer_id
            )

        if status:
            conditions.append(
                TechnicianAssignment.status ==
                status
            )

        if search:
            conditions.append(
                Technician.full_name.ilike(
                    f"%{search}%"
                )
            )

        statement = (
            select(
                Technician.id.label(
                    "technician_id"
                ),
                Technician.full_name.label(
                    "technician_name"
                ),
                func.count(
                    TechnicianAssignment.id
                ).label(
                    "total_assignments"
                ),
                func.count(
                    TechnicianAssignment.id
                ).filter(
                    TechnicianAssignment.status
                    == TechnicianJobStatus.COMPLETED.value
                ).label(
                    "completed_assignments"
                ),
            )
            .join(
                TechnicianAssignment,
                TechnicianAssignment.technician_id ==
                Technician.id,
            )
            .where(*conditions)
            .group_by(
                Technician.id,
                Technician.full_name,
            )
        )

        if sort_order.lower() == "asc":
            statement = statement.order_by(
                func.count(
                    TechnicianAssignment.id
                ).asc()
            )
        else:
            statement = statement.order_by(
                func.count(
                    TechnicianAssignment.id
                ).desc()
            )

        return self._paginate(
            statement,
            db,
            page,
            page_size,
        )

    # ---------------------------------------------------------
    # CUSTOMER SERVICE
    # ---------------------------------------------------------

    def customer_service(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        customer_id=None,
        status=None,
        search=None,
        page=1,
        page_size=20,
        sort_order="desc",
    ):
        conditions = []

        if start_date:
            conditions.append(
                ServiceRequest.created_at >=
                datetime.combine(
                    start_date,
                    time.min,
                ).replace(
                    tzinfo=timezone.utc
                )
            )

        if end_date:
            conditions.append(
                ServiceRequest.created_at <=
                datetime.combine(
                    end_date,
                    time.max,
                ).replace(
                    tzinfo=timezone.utc
                )
            )

        if customer_id:
            conditions.append(
                ServiceRequest.customer_id ==
                customer_id
            )

        if status:
            conditions.append(
                ServiceRequest.status == status
            )

        if search:
            conditions.append(
                ServiceRequest.request_number.ilike(
                    f"%{search}%"
                )
            )

        statement = (
            select(
                func.date(
                    ServiceRequest.created_at
                ).label("date"),
                func.count(
                    ServiceRequest.id
                ).label(
                    "total_requests"
                ),
                func.count(
                    ServiceRequest.id
                ).filter(
                    ServiceRequest.status ==
                    ServiceRequestStatus.COMPLETED
                ).label(
                    "completed_requests"
                ),
                func.count(
                    ServiceRequest.id
                ).filter(
                    ServiceRequest.status ==
                    ServiceRequestStatus.REJECTED
                ).label(
                    "rejected_requests"
                ),
            )
            .where(*conditions)
            .group_by(
                func.date(
                    ServiceRequest.created_at
                )
            )
        )

        if sort_order.lower() == "asc":
            statement = statement.order_by(
                func.date(
                    ServiceRequest.created_at
                ).asc()
            )
        else:
            statement = statement.order_by(
                func.date(
                    ServiceRequest.created_at
                ).desc()
            )

        return self._paginate(
            statement,
            db,
            page,
            page_size,
        )