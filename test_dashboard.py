import os
from datetime import date, timedelta
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "telecom_service_network_test"
)

from fastapi.testclient import TestClient

from db.database import Base, SessionLocal, engine
from main import app

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
from models.user import User

from utils.enums import (
    KYCStatus,
    PlanStatus,
    PlanType,
    ServiceRequestStatus,
    ServiceRequestType,
    SIMStatus,
    SIMType,
    SubscriptionStatus,
    TechnicianAvailability,
    TechnicianJobStatus,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    UsageType,
    UserRole,
)


client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    engine.dispose()


def unique_email(prefix="dashboard"):
    return f"{prefix}_{uuid4().hex}@example.com"


def unique_value(prefix="TEST"):
    return f"{prefix}-{uuid4().hex[:10]}"


def create_user(
    role=UserRole.CUSTOMER,
    email=None,
    full_name="Dashboard User",
):
    db = SessionLocal()

    try:
        user = User(
            full_name=full_name,
            email=email or unique_email(),
            phone=f"9{uuid4().int % 10**9:09d}",
            password_hash="test-password-hash",
            role=role,
            is_active=True,
            is_verified=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    finally:
        db.close()


def create_customer(
    active=True,
    email=None,
):
    db = SessionLocal()

    try:
        user = User(
            full_name="Dashboard Customer",
            email=email or unique_email("customer"),
            phone=f"9{uuid4().int % 10**9:09d}",
            password_hash="test-password-hash",
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=True,
        )

        db.add(user)
        db.flush()

        customer = Customer(
            user_id=user.id,
            customer_number=unique_value("CUST"),
            address_line1="Dashboard Street",
            city="Tirupati",
            state="Andhra Pradesh",
            postal_code="517501",
            kyc_status=KYCStatus.VERIFIED,
            is_active=active,
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        return customer

    finally:
        db.close()


def create_plan(
    price=499.0,
    data_limit_mb=10000,
):
    db = SessionLocal()

    try:
        plan = Plan(
            plan_name=unique_value("PLAN"),
            description="Dashboard test plan",
            plan_type=PlanType.PREPAID,
            validity_days=30,
            data_limit_mb=data_limit_mb,
            voice_limit_minutes=1000,
            sms_limit=100,
            price=price,
            status=PlanStatus.ACTIVE,
        )

        db.add(plan)
        db.commit()
        db.refresh(plan)

        return plan

    finally:
        db.close()


def create_sim(
    customer_id=None,
    plan_id=None,
    status=SIMStatus.ACTIVE,
):
    db = SessionLocal()

    try:
        sim = SIM(
            sim_number=unique_value("SIM"),
            sim_type=SIMType.PHYSICAL,
            status=status,
            activation_date=date.today(),
            customer_id=customer_id,
            plan_id=plan_id,
        )

        db.add(sim)
        db.commit()
        db.refresh(sim)

        return sim

    finally:
        db.close()


def create_subscription(
    customer_id,
    sim_id,
    plan_id,
    status=SubscriptionStatus.ACTIVE,
):
    db = SessionLocal()

    try:
        subscription = Subscription(
            customer_id=customer_id,
            sim_id=sim_id,
            plan_id=plan_id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status=status,
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        return subscription

    finally:
        db.close()


def create_usage(
    customer_id,
    sim_id,
    subscription_id,
    quantity=500.0,
):
    db = SessionLocal()

    try:
        usage = Usage(
            customer_id=customer_id,
            sim_id=sim_id,
            subscription_id=subscription_id,
            usage_type=UsageType.DATA,
            usage_date=date.today(),
            quantity=quantity,
        )

        db.add(usage)
        db.commit()
        db.refresh(usage)

        return usage

    finally:
        db.close()


def create_outage(
    open_outage=True,
):
    db = SessionLocal()

    try:
        outage = NetworkOutage(
            outage_code=unique_value("OUTAGE"),
            outage_type="Network",
            description="Dashboard test outage",
            severity="HIGH",
            start_time=date.today(),
            expected_resolution=None,
            actual_resolution=None
            if open_outage
            else date.today(),
        )

        db.add(outage)
        db.commit()
        db.refresh(outage)

        return outage

    finally:
        db.close()


def create_ticket(
    customer_id,
    status=TicketStatus.OPEN,
):
    db = SessionLocal()

    try:
        ticket = SupportTicket(
            ticket_number=unique_value("TICKET"),
            customer_id=customer_id,
            category=TicketCategory.NETWORK_ISSUE,
            subject="Dashboard test ticket",
            description="Dashboard test ticket description",
            priority=TicketPriority.HIGH,
            status=status,
            escalation_level=0,
            is_escalated=False,
        )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        return ticket

    finally:
        db.close()


def create_sla_rule():
    db = SessionLocal()

    try:
        rule = SLARule(
            rule_name=unique_value("SLA"),
            ticket_category=TicketCategory.NETWORK_ISSUE,
            priority=TicketPriority.HIGH,
            customer_type="Customer",
            sla_minutes=60,
            warning_minutes=30,
            escalation_enabled=True,
            is_active=True,
        )

        db.add(rule)
        db.commit()
        db.refresh(rule)

        return rule

    finally:
        db.close()


def create_ticket_sla(
    ticket_id,
    sla_rule_id,
    breached=False,
):
    db = SessionLocal()

    try:
        now = date.today()

        ticket_sla = TicketSLA(
            ticket_id=ticket_id,
            sla_rule_id=sla_rule_id,
            start_time=now,
            deadline=now,
            resolution_time=None,
            resolution_minutes=None,
            status="Active",
            is_breached=breached,
            escalation_status=None,
            escalated_at=None,
        )

        db.add(ticket_sla)
        db.commit()
        db.refresh(ticket_sla)

        return ticket_sla

    finally:
        db.close()


def create_technician():
    db = SessionLocal()

    try:
        user = User(
            full_name="Dashboard Technician",
            email=unique_email("technician"),
            phone=f"8{uuid4().int % 10**9:09d}",
            password_hash="test-password-hash",
            role=UserRole.FIELD_TECHNICIAN,
            is_active=True,
            is_verified=True,
        )

        db.add(user)
        db.flush()

        technician = Technician(
            user_id=user.id,
            employee_id=unique_value("EMP"),
            full_name="Dashboard Technician",
            phone=user.phone,
            availability=TechnicianAvailability.AVAILABLE.value,
            service_area="Tirupati",
            address="Dashboard Technician Address",
        )

        db.add(technician)
        db.commit()
        db.refresh(technician)

        return technician

    finally:
        db.close()


def create_technician_assignment(
    technician_id,
    customer_id,
    status=TechnicianJobStatus.ASSIGNED,
):
    db = SessionLocal()

    try:
        assignment = TechnicianAssignment(
            technician_id=technician_id,
            customer_id=customer_id,
            job_type="SERVICE",
            job_reference_id=None,
            description="Dashboard technician assignment",
            status=status.value,
            assigned_at=date.today(),
            started_at=None,
            completed_at=None,
            notes=None,
        )

        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        return assignment

    finally:
        db.close()


def create_tower(status="Active"):
    db = SessionLocal()

    try:
        tower = Tower(
            tower_code=unique_value("TOWER"),
            tower_name="Dashboard Tower",
            tower_type="Macro",
            latitude=13.6288,
            longitude=79.4192,
            address="Tirupati",
            coverage_area=10.0,
            capacity=1000,
            status=status,
        )

        db.add(tower)
        db.commit()
        db.refresh(tower)

        return tower

    finally:
        db.close()


def create_service_request(
    customer_id,
    user_id,
    status=ServiceRequestStatus.PENDING,
):
    db = SessionLocal()

    try:
        request = ServiceRequest(
            request_number=unique_value("REQ"),
            customer_id=customer_id,
            request_type=ServiceRequestType.PLAN_CHANGE,
            status=status,
            reason="Dashboard test",
            description="Dashboard service request",
            created_by=user_id,
        )

        db.add(request)
        db.commit()
        db.refresh(request)

        return request

    finally:
        db.close()


def create_admin():
    email = unique_email("admin")
    password = "Admin@12345"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Dashboard Admin",
            "email": email,
            "phone": f"7{uuid4().int % 10**9:09d}",
            "password": password,
            "role": "Super Admin",
        },
    )

    if response.status_code not in [200, 201]:
        raise AssertionError(
            f"Admin registration failed: "
            f"{response.status_code} - {response.text}"
        )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    if login_response.status_code != 200:
        raise AssertionError(
            f"Admin login failed: "
            f"{login_response.status_code} - "
            f"{login_response.text}"
        )

    body = login_response.json()

    return {
        "token": body["access_token"],
        "user_id": body.get("user_id"),
    }


def test_dashboard_requires_authentication():
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 401


def test_dashboard_returns_all_sections():
    admin = create_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "customers" in data
    assert "subscriptions" in data
    assert "sims" in data
    assert "usage" in data
    assert "outages" in data
    assert "tickets" in data
    assert "sla" in data
    assert "technicians" in data
    assert "towers" in data
    assert "service_requests" in data
    assert "plans" in data


def test_dashboard_customer_counts():
    admin = create_admin()

    create_customer(active=True)
    create_customer(active=True)
    create_customer(active=False)

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customers"]["total_customers"] == 3
    assert data["customers"]["active_customers"] == 2


def test_dashboard_active_subscription_count():
    admin = create_admin()

    customer = create_customer()
    plan = create_plan()

    sim = create_sim(
        customer_id=customer.id,
        plan_id=plan.id,
    )

    create_subscription(
        customer_id=customer.id,
        sim_id=sim.id,
        plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE,
    )

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["subscriptions"]["active_subscriptions"] == 1


def test_dashboard_active_sim_count():
    admin = create_admin()

    customer = create_customer()

    create_sim(
        customer_id=customer.id,
        status=SIMStatus.ACTIVE,
    )

    create_sim(
        customer_id=customer.id,
        status=SIMStatus.AVAILABLE,
    )

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sims"]["active_sims"] == 1


def test_dashboard_data_usage():
    admin = create_admin()

    customer = create_customer()
    plan = create_plan()

    sim = create_sim(
        customer_id=customer.id,
        plan_id=plan.id,
    )

    subscription = create_subscription(
        customer_id=customer.id,
        sim_id=sim.id,
        plan_id=plan.id,
    )

    create_usage(
        customer_id=customer.id,
        sim_id=sim.id,
        subscription_id=subscription.id,
        quantity=1000.0,
    )

    create_usage(
        customer_id=customer.id,
        sim_id=sim.id,
        subscription_id=subscription.id,
        quantity=500.0,
    )

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["usage"]["total_data_usage"] == 1500.0


def test_dashboard_network_outages():
    admin = create_admin()

    create_outage(open_outage=True)
    create_outage(open_outage=False)

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["outages"]["total_outages"] == 2
    assert data["outages"]["open_outages"] == 1


def test_dashboard_open_tickets():
    admin = create_admin()

    customer = create_customer()

    create_ticket(
        customer_id=customer.id,
        status=TicketStatus.OPEN,
    )

    create_ticket(
        customer_id=customer.id,
        status=TicketStatus.IN_PROGRESS,
    )

    create_ticket(
        customer_id=customer.id,
        status=TicketStatus.CLOSED,
    )

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tickets"]["open_tickets"] == 2


def test_dashboard_sla_records_and_breaches():
    admin = create_admin()

    customer = create_customer()

    ticket_1 = create_ticket(
        customer.id,
        TicketStatus.OPEN,
    )

    ticket_2 = create_ticket(
        customer.id,
        TicketStatus.OPEN,
    )

    rule = create_sla_rule()

    create_ticket_sla(
        ticket_id=ticket_1.id,
        sla_rule_id=rule.id,
        breached=True,
    )

    create_ticket_sla(
        ticket_id=ticket_2.id,
        sla_rule_id=rule.id,
        breached=False,
    )

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sla"]["total_sla_records"] == 2
    assert data["sla"]["breached_slas"] == 1


def test_dashboard_technician_workload():
    admin = create_admin()

    customer = create_customer()

    technician = create_technician()

    create_technician_assignment(
        technician_id=technician.id,
        customer_id=customer.id,
        status=TechnicianJobStatus.ASSIGNED,
    )

    create_technician_assignment(
        technician_id=technician.id,
        customer_id=customer.id,
        status=TechnicianJobStatus.IN_PROGRESS,
    )

    create_technician_assignment(
        technician_id=technician.id,
        customer_id=customer.id,
        status=TechnicianJobStatus.COMPLETED,
    )

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["technicians"]) == 1

    technician_data = data["technicians"][0]

    assert technician_data["technician_id"] == technician.id
    assert technician_data["technician_name"] == technician.full_name
    assert technician_data["total_assignments"] == 3
    assert technician_data["active_assignments"] == 2
    assert technician_data["completed_assignments"] == 1


def test_dashboard_tower_status():
    admin = create_admin()

    create_tower("Active")
    create_tower("Maintenance")
    create_tower("Offline")
    create_tower("Decommissioned")

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    towers = data["towers"]

    assert towers["total_towers"] == 4
    assert towers["active_towers"] == 1
    assert towers["maintenance_towers"] == 1
    assert towers["offline_towers"] == 1
    assert towers["decommissioned_towers"] == 1


def test_dashboard_service_requests():
    admin = create_admin()

    customer = create_customer()

    user = create_user(
        role=UserRole.SUPER_ADMIN,
        full_name="Dashboard Request Creator",
    )

    create_service_request(
        customer_id=customer.id,
        user_id=user.id,
        status=ServiceRequestStatus.PENDING,
    )

    create_service_request(
        customer_id=customer.id,
        user_id=user.id,
        status=ServiceRequestStatus.IN_PROGRESS,
    )

    create_service_request(
        customer_id=customer.id,
        user_id=user.id,
        status=ServiceRequestStatus.APPROVED,
    )

    create_service_request(
        customer_id=customer.id,
        user_id=user.id,
        status=ServiceRequestStatus.COMPLETED,
    )

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    requests = data["service_requests"]

    assert requests["total_service_requests"] == 4
    assert requests["pending_requests"] == 1
    assert requests["in_progress_requests"] == 1
    assert requests["approved_requests"] == 1
    assert requests["completed_requests"] == 1
    assert requests["rejected_requests"] == 0
    assert requests["cancelled_requests"] == 0


def test_dashboard_plan_utilization():
    admin = create_admin()

    customer = create_customer()

    plan = create_plan(
        price=599.0,
        data_limit_mb=15000,
    )

    sim = create_sim(
        customer_id=customer.id,
        plan_id=plan.id,
    )

    create_subscription(
        customer_id=customer.id,
        sim_id=sim.id,
        plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE,
    )

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    plans = data["plans"]

    assert len(plans) == 1

    plan_data = plans[0]

    assert plan_data["plan_id"] == plan.id
    assert plan_data["plan_name"] == plan.plan_name
    assert plan_data["active_subscriptions"] == 1
    assert plan_data["data_limit_mb"] == 15000


def test_dashboard_empty_database_returns_zero_counts():
    admin = create_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customers"]["total_customers"] == 0
    assert data["customers"]["active_customers"] == 0

    assert data["subscriptions"]["active_subscriptions"] == 0

    assert data["sims"]["active_sims"] == 0

    assert data["usage"]["total_data_usage"] == 0.0

    assert data["outages"]["total_outages"] == 0
    assert data["outages"]["open_outages"] == 0

    assert data["tickets"]["open_tickets"] == 0

    assert data["sla"]["total_sla_records"] == 0
    assert data["sla"]["breached_slas"] == 0

    assert data["technicians"] == []

    assert data["towers"]["total_towers"] == 0
    assert data["towers"]["active_towers"] == 0
    assert data["towers"]["maintenance_towers"] == 0
    assert data["towers"]["offline_towers"] == 0
    assert data["towers"]["decommissioned_towers"] == 0

    assert data["service_requests"]["total_service_requests"] == 0

    assert data["plans"] == []