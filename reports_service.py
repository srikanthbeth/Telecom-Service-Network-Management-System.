from datetime import date

from sqlalchemy.orm import Session

from repositories.reports_repository import ReportsRepository


class ReportsService:
    def __init__(self):
        self.repository = ReportsRepository()

    def _build_response(
        self,
        result,
        page: int,
        page_size: int,
    ):
        rows, total, total_pages = result

        items = []

        for row in rows:
            if hasattr(row, "_mapping"):
                items.append(dict(row._mapping))
            elif isinstance(row, dict):
                items.append(row)
            else:
                items.append(dict(row))

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }

    def get_customer_growth(
        self,
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        location: str | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ):
        result = self.repository.customer_growth(
            db=db,
            start_date=start_date,
            end_date=end_date,
            location=location,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        return self._build_response(
            result,
            page,
            page_size,
        )

    def get_subscription_trends(
        self,
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        plan_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ):
        result = self.repository.subscription_trends(
            db=db,
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
            plan_id=plan_id,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        return self._build_response(
            result,
            page,
            page_size,
        )

    def get_plan_popularity(
        self,
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        plan_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ):
        result = self.repository.plan_popularity(
            db=db,
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
            plan_id=plan_id,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        return self._build_response(
            result,
            page,
            page_size,
        )

    def get_data_consumption(
        self,
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        plan_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ):
        result = self.repository.data_consumption(
            db=db,
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
            plan_id=plan_id,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        return self._build_response(
            result,
            page,
            page_size,
        )

    def get_network_uptime(
        self,
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ):
        result = self.repository.network_uptime(
            db=db,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        return self._build_response(
            result,
            page,
            page_size,
        )

    def get_outage_frequency(
        self,
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ):
        result = self.repository.outage_frequency(
            db=db,
            start_date=start_date,
            end_date=end_date,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        return self._build_response(
            result,
            page,
            page_size,
        )

    def get_ticket_resolution(
        self,
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ):
        result = self.repository.ticket_resolution(
            db=db,
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        return self._build_response(
            result,
            page,
            page_size,
        )

    def get_sla_performance(
        self,
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ):
        result = self.repository.sla_performance(
            db=db,
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        return self._build_response(
            result,
            page,
            page_size,
        )

    def get_technician_performance(
        self,
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ):
        result = self.repository.technician_performance(
            db=db,
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        return self._build_response(
            result,
            page,
            page_size,
        )

    def get_customer_service(
        self,
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ):
        result = self.repository.customer_service(
            db=db,
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        return self._build_response(
            result,
            page,
            page_size,
        )