from fastapi import FastAPI


from models.support_ticket import SupportTicket
from models.ticket_comment import TicketComment
from models.ticket_history import TicketHistory
from models.sla_rule import SLARule
from models.ticket_sla import TicketSLA
from models.service_request import ServiceRequest
from models.service_request_history import ServiceRequestHistory



from routes.auth import router as auth_router
from routes.customers import router as customers_router
from routes.plans import router as plans_router
from routes.sims import router as sims_router
from routes.devices import router as devices_router
from routes.subscriptions import router as subscriptions_router
from routes.usage import router as usage_router
from routes.towers import router as tower_router
from routes.equipment import router as equipment_router
from routes.outages import router as outages_router
from routes.technicians import router as technicians_router
from routes.support_tickets import router as support_tickets_router
from routes.sla import router as sla_router
from routes.service_requests import (
    router as service_requests_router,
)

from routes.dashboard import router as dashboard_router
from routes.reports import router as reports_router
from routes.audit_logs import router as audit_logs_router


app = FastAPI(
    title="Telecom Service & Network Management System",
    description=(
        "Advanced FastAPI backend for telecom "
        "service and network management."
    ),
    version="1.0.0",
)


app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    customers_router,
    prefix="/api/v1",
)

app.include_router(
    plans_router,
    prefix="/api/v1",
)

app.include_router(
    sims_router,
    prefix="/api/v1",
)



app.include_router(
    devices_router,
    prefix="/api/v1",
)

app.include_router(
    subscriptions_router,
    prefix="/api/v1",
)

app.include_router(
    usage_router,
    prefix="/api/v1",
)


app.include_router(
    tower_router,
    prefix="/api/v1",
)

app.include_router(
    equipment_router,
    prefix="/api/v1",
)

app.include_router(
    outages_router,
    prefix="/api/v1",
)


app.include_router(
    technicians_router,
    prefix="/api/v1",
)

app.include_router(
    support_tickets_router,
    prefix="/api/v1",
)

app.include_router(
    sla_router,
    prefix="/api/v1",
)

app.include_router(
    service_requests_router,
    prefix="/api/v1",
)
app.include_router(
    dashboard_router,
    prefix="/api/v1",
)

app.include_router(
    reports_router,
    prefix="/api/v1",
)

app.include_router(
    audit_logs_router,
    prefix="/api/v1",
)

@app.get("/")
def root():
    return {
        "message": (
            "Telecom Service & Network "
            "Management API"
        )
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }