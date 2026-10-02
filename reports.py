
from datetime import date as Date

from pydantic import BaseModel, ConfigDict, Field


class ReportQuery(BaseModel):
    start_date: Date | None = None
    end_date: Date | None = None

    customer_id: int | None = None
    plan_id: int | None = None

    location: str | None = None
    status: str | None = None

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    sort_by: str = "date"
    sort_order: str = "desc"

    search: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ReportItem(BaseModel):
    date: Date | None = None
    label: str | None = None
    count: int = 0
    value: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class PaginatedReport(BaseModel):
    items: list[dict]
    page: int
    page_size: int
    total: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class CustomerGrowthReport(PaginatedReport):
    pass


class SubscriptionTrendReport(PaginatedReport):
    pass


class PlanPopularityReport(PaginatedReport):
    pass


class DataConsumptionReport(PaginatedReport):
    pass


class NetworkUptimeReport(PaginatedReport):
    pass


class OutageFrequencyReport(PaginatedReport):
    pass


class TicketResolutionReport(PaginatedReport):
    pass


class SLAPerformanceReport(PaginatedReport):
    pass


class TechnicianPerformanceReport(PaginatedReport):
    pass


class CustomerServiceReport(PaginatedReport):
    pass

