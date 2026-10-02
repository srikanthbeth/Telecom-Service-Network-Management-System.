from pydantic import BaseModel, ConfigDict


class CustomerDashboard(BaseModel):
    total_customers: int
    active_customers: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class SubscriptionDashboard(BaseModel):
    active_subscriptions: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class SIMDashboard(BaseModel):
    active_sims: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class UsageDashboard(BaseModel):
    total_data_usage: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class OutageDashboard(BaseModel):
    total_outages: int
    open_outages: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class TicketDashboard(BaseModel):
    open_tickets: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class SLADashboard(BaseModel):
    total_sla_records: int
    breached_slas: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class TechnicianWorkload(BaseModel):
    technician_id: int
    technician_name: str
    total_assignments: int
    active_assignments: int
    completed_assignments: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class TowerDashboard(BaseModel):
    total_towers: int
    active_towers: int
    maintenance_towers: int
    offline_towers: int
    decommissioned_towers: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class ServiceRequestDashboard(BaseModel):
    total_service_requests: int
    pending_requests: int
    in_progress_requests: int
    approved_requests: int
    rejected_requests: int
    completed_requests: int
    cancelled_requests: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class PlanUtilization(BaseModel):
    plan_id: int
    plan_name: str
    active_subscriptions: int
    data_limit_mb: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class DashboardResponse(BaseModel):
    customers: CustomerDashboard
    subscriptions: SubscriptionDashboard
    sims: SIMDashboard
    usage: UsageDashboard
    outages: OutageDashboard
    tickets: TicketDashboard
    sla: SLADashboard
    technicians: list[TechnicianWorkload]
    towers: TowerDashboard
    service_requests: ServiceRequestDashboard
    plans: list[PlanUtilization]

    model_config = ConfigDict(
        from_attributes=True,
    )