from sqlalchemy.orm import Session

from repositories.dashboard_repository import DashboardRepository


class DashboardService:

    def __init__(self):
        self.repository = DashboardRepository()

    def get_dashboard(self, db: Session):
        service_requests = (
            self.repository.get_service_request_counts(db)
        )

        return {
            "customers": {
                "total_customers": (
                    self.repository.get_total_customers(db)
                ),
                "active_customers": (
                    self.repository.get_active_customers(db)
                ),
            },

            "subscriptions": {
                "active_subscriptions": (
                    self.repository.get_active_subscriptions(db)
                ),
            },

            "sims": {
                "active_sims": (
                    self.repository.get_active_sims(db)
                ),
            },

            "usage": {
                "total_data_usage": (
                    self.repository.get_total_data_usage(db)
                ),
            },

            "outages": {
                "total_outages": (
                    self.repository.get_total_outages(db)
                ),
                "open_outages": (
                    self.repository.get_open_outages(db)
                ),
            },

            "tickets": {
                "open_tickets": (
                    self.repository.get_open_tickets(db)
                ),
            },

            "sla": {
                "total_sla_records": (
                    self.repository.get_total_sla_records(db)
                ),
                "breached_slas": (
                    self.repository.get_breached_slas(db)
                ),
            },

            "technicians": (
                self.repository.get_technician_workload(db)
            ),

            "towers": {
                "total_towers": (
                    self.repository.get_total_towers(db)
                ),
                "active_towers": (
                    self.repository.get_active_towers(db)
                ),
                "maintenance_towers": (
                    self.repository.get_maintenance_towers(db)
                ),
                "offline_towers": (
                    self.repository.get_offline_towers(db)
                ),
                "decommissioned_towers": (
                    self.repository.get_decommissioned_towers(db)
                ),
            },

            "service_requests": service_requests,

            "plans": (
                self.repository.get_plan_utilization(db)
            ),
        }