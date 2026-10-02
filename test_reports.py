import os
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "telecom_service_network_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import text

from db.database import Base, SessionLocal, engine
from main import app

from models.user import User
from models.customer import Customer
from models.plan import Plan
from models.sim import SIM
from models.subscription import Subscription
from models.usage import Usage
from models.network_outage import NetworkOutage
from models.support_ticket import SupportTicket
from models.ticket_sla import TicketSLA
from models.sla_rule import SLARule
from models.technician import Technician
from models.technician_assignment import TechnicianAssignment
from models.service_request import ServiceRequest

from utils.enums import (
    UserRole,
    AccountStatus,
    KYCStatus,
    PlanType,
    PlanStatus,
    SIMType,
    SIMStatus,
    SubscriptionStatus,
    UsageType,
    OutageSeverity,
    TicketStatus,
    TicketPriority,
    TicketCategory,
    TechnicianAvailability,
    TechnicianJobStatus,
    SLAStatus,
    SLAEscalationStatus,
    ServiceRequestType,
    ServiceRequestStatus,
)

client = TestClient(app)


# ============================================================
# DATABASE SETUP
# ============================================================

def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    engine.dispose()


# ============================================================
# HELPERS
# ============================================================

def unique_email(prefix="user"):
    return f"{prefix}_{uuid4().hex[:10]}@example.com"


def register_user(
    role=UserRole.CUSTOMER.value,
    email=None,
    full_name="Test User",
):
    email = email or unique_email()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "phone": f"9{uuid4().int % 1000000000:09d}",
            "password": "Test@12345",
            "role": role,
        },
    )

    assert response.status_code in [200, 201], response.text

    return {
        "email": email,
        "password": "Test@12345",
        "data": response.json(),
    }


def login_user(email, password="Test@12345"):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    token = data.get("access_token")

    assert token is not None

    return token


def create_admin():
    user = register_user(
        role=UserRole.SUPER_ADMIN.value,
        full_name="Reports Admin",
    )

    token = login_user(
        user["email"],
        user["password"],
    )

    return token


def create_customer(
    session,
    city="Tirupati",
    state="Andhra Pradesh",
    country="India",
    created_at=None,
    is_active=True,
):
    user = User(
        full_name=f"Customer {uuid4().hex[:6]}",
        email=unique_email("customer"),
        phone=f"9{uuid4().int % 1000000000:09d}",
        password_hash="dummy_hash",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
    )

    session.add(user)
    session.flush()

    customer = Customer(
        user_id=user.id,
        customer_number=f"CUST-{uuid4().hex[:8].upper()}",
        address_line1="Test Address",
        address_line2=None,
        city=city,
        state=state,
        postal_code="517501",
        country=country,
        kyc_status=KYCStatus.VERIFIED,
        is_active=is_active,
    )

    if created_at is not None:
        customer.created_at = created_at

    session.add(customer)
    session.flush()

    return customer


def create_plan(
    session,
    plan_name=None,
    price=499.0,
    status=PlanStatus.ACTIVE,
):
    plan = Plan(
        plan_name=plan_name or f"Plan-{uuid4().hex[:8]}",
        description="Test plan",
        plan_type=PlanType.PREPAID,
        validity_days=30,
        data_limit_mb=10000,
        voice_limit_minutes=1000,
        sms_limit=100,
        price=price,
        status=status,
    )

    session.add(plan)
    session.flush()

    return plan


def create_sim(session, customer):
    sim = SIM(
        sim_number=f"SIM-{uuid4().hex[:12].upper()}",
        sim_type=SIMType.PHYSICAL,
        status=SIMStatus.ACTIVE,
        activation_date=date.today(),
        customer_id=customer.id,
        plan_id=None,
        tower_id=None,
    )

    session.add(sim)
    session.flush()

    return sim


def create_subscription(
    session,
    customer,
    plan,
    sim,
    start_date_value=None,
    status=SubscriptionStatus.ACTIVE,
):
    start_date_value = start_date_value or date.today()

    subscription = Subscription(
        customer_id=customer.id,
        sim_id=sim.id,
        plan_id=plan.id,
        start_date=start_date_value,
        end_date=start_date_value + timedelta(days=30),
        status=status,
    )

    session.add(subscription)
    session.flush()

    return subscription


def create_usage(
    session,
    customer,
    sim,
    subscription,
    usage_date_value,
    quantity=100.0,
    usage_type=UsageType.DATA,
):
    usage = Usage(
        customer_id=customer.id,
        sim_id=sim.id,
        subscription_id=subscription.id,
        usage_type=usage_type,
        usage_date=usage_date_value,
        quantity=quantity,
    )

    session.add(usage)
    session.flush()

    return usage


def create_outage(
    session,
    start_time,
    actual_resolution,
    severity=OutageSeverity.HIGH,
    outage_type="Network",
):
    outage = NetworkOutage(
        outage_code=f"OUT-{uuid4().hex[:8].upper()}",
        outage_type=outage_type,
        description="Test network outage",
        severity=severity,
        start_time=start_time,
        expected_resolution=actual_resolution,
        actual_resolution=actual_resolution,
    )

    session.add(outage)
    session.flush()

    return outage


def create_ticket(
    session,
    customer,
    created_at,
    resolved_at=None,
    status=TicketStatus.OPEN,
):
    ticket = SupportTicket(
        ticket_number=f"TKT-{uuid4().hex[:8].upper()}",
        customer_id=customer.id,
        category=TicketCategory.NETWORK_ISSUE,
        subject="Test network issue",
        description="Test support ticket",
        priority=TicketPriority.HIGH,
        status=status,
        assigned_agent_id=None,
        assigned_technician_id=None,
        escalation_level=0,
        is_escalated=False,
        resolution_notes=None,
        resolved_at=resolved_at,
        closed_at=None,
    )

    ticket.created_at = created_at

    session.add(ticket)
    session.flush()

    return ticket


def create_sla_rule(session):
    rule = SLARule(
        rule_name=f"SLA-{uuid4().hex[:8]}",
        ticket_category=TicketCategory.NETWORK_ISSUE,
        priority=TicketPriority.HIGH,
        customer_type="Customer",
        sla_minutes=60,
        warning_minutes=30,
        escalation_enabled=True,
        is_active=True,
    )

    session.add(rule)
    session.flush()

    return rule


def create_ticket_sla(
    session,
    ticket,
    sla_rule,
    start_time,
    resolution_minutes=30,
    is_breached=False,
):
    ticket_sla = TicketSLA(
        ticket_id=ticket.id,
        sla_rule_id=sla_rule.id,
        start_time=start_time,
        deadline=start_time + timedelta(minutes=60),
        resolution_time=start_time + timedelta(minutes=resolution_minutes),
        resolution_minutes=resolution_minutes,
        status=(
            SLAStatus.BREACHED.value
            if is_breached
            else SLAStatus.RESOLVED.value
        ),
        is_breached=is_breached,
        escalation_status=(
            SLAEscalationStatus.ESCALATED.value
            if is_breached
            else SLAEscalationStatus.NOT_ESCALATED.value
        ),
        escalated_at=(
            start_time + timedelta(minutes=61)
            if is_breached
            else None
        ),
    )

    session.add(ticket_sla)
    session.flush()

    return ticket_sla


def create_technician(session):
    user = User(
        full_name=f"Technician {uuid4().hex[:6]}",
        email=unique_email("technician"),
        phone=f"8{uuid4().int % 1000000000:09d}",
        password_hash="dummy_hash",
        role=UserRole.FIELD_TECHNICIAN,
        is_active=True,
        is_verified=True,
    )

    session.add(user)
    session.flush()

    technician = Technician(
        user_id=user.id,
        employee_id=f"EMP-{uuid4().hex[:8].upper()}",
        full_name=user.full_name,
        phone=user.phone,
        availability=TechnicianAvailability.AVAILABLE.value,
        latitude=13.6288,
        longitude=79.4192,
        service_area="Tirupati",
        address="Test Technician Address",
    )

    session.add(technician)
    session.flush()

    return technician


def create_assignment(
    session,
    technician,
    customer,
    assigned_at,
    status=TechnicianJobStatus.COMPLETED,
):
    assignment = TechnicianAssignment(
        technician_id=technician.id,
        customer_id=customer.id,
        job_type="Network Repair",
        job_reference_id=customer.id,
        description="Test technician assignment",
        status=status.value,
        assigned_at=assigned_at,
        started_at=assigned_at + timedelta(minutes=10),
        completed_at=(
            assigned_at + timedelta(minutes=60)
            if status == TechnicianJobStatus.COMPLETED
            else None
        ),
        notes="Test assignment",
        assigned_by=None,
    )

    session.add(assignment)
    session.flush()

    return assignment


def create_service_request(
    session,
    customer,
    created_by,
    created_at,
    status=ServiceRequestStatus.COMPLETED,
):
    request = ServiceRequest(
        request_number=f"REQ-{uuid4().hex[:8].upper()}",
        customer_id=customer.id,
        request_type=ServiceRequestType.PLAN_CHANGE,
        status=status,
        reason="Test request",
        description="Test customer service request",
        created_by=created_by,
        completed_at=(
            created_at + timedelta(hours=2)
            if status == ServiceRequestStatus.COMPLETED
            else None
        ),
    )

    request.created_at = created_at

    session.add(request)
    session.flush()

    return request


# ============================================================
# 1. CUSTOMER GROWTH
# ============================================================

def test_customer_growth_report():
    token = create_admin()

    session = SessionLocal()

    try:
        customer1 = create_customer(
            session,
            created_at=datetime(
                2026,
                1,
                5,
                tzinfo=timezone.utc,
            ),
        )

        customer2 = create_customer(
            session,
            created_at=datetime(
                2026,
                1,
                15,
                tzinfo=timezone.utc,
            ),
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/customer-growth",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["total"] >= 1

    finally:
        session.close()


# ============================================================
# 2. SUBSCRIPTION TRENDS
# ============================================================

def test_subscription_trends_report():
    token = create_admin()

    session = SessionLocal()

    try:
        customer = create_customer(session)
        plan = create_plan(session)
        sim = create_sim(session, customer)

        create_subscription(
            session,
            customer,
            plan,
            sim,
            start_date_value=date(2026, 2, 1),
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/subscription-trends",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-03-01",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data
        assert data["total"] >= 1

    finally:
        session.close()


# ============================================================
# 3. PLAN POPULARITY
# ============================================================

def test_plan_popularity_report():
    token = create_admin()

    session = SessionLocal()

    try:
        customer1 = create_customer(session)
        customer2 = create_customer(session)

        plan = create_plan(
            session,
            plan_name="Popular-Test-Plan",
        )

        sim1 = create_sim(session, customer1)
        sim2 = create_sim(session, customer2)

        create_subscription(
            session,
            customer1,
            plan,
            sim1,
            start_date_value=date(2026, 3, 1),
        )

        create_subscription(
            session,
            customer2,
            plan,
            sim2,
            start_date_value=date(2026, 3, 2),
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/plan-popularity",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-04-01",
                "search": "Popular-Test-Plan",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data
        assert data["total"] >= 1

        item = data["items"][0]

        assert (
            item.get("plan_name") == "Popular-Test-Plan"
            or item.get("label") == "Popular-Test-Plan"
        )

    finally:
        session.close()


# ============================================================
# 4. DATA CONSUMPTION
# ============================================================

def test_data_consumption_report():
    token = create_admin()

    session = SessionLocal()

    try:
        customer = create_customer(
            session,
            city="Tirupati",
        )

        plan = create_plan(session)

        sim = create_sim(session, customer)

        subscription = create_subscription(
            session,
            customer,
            plan,
            sim,
            start_date_value=date(2026, 4, 1),
        )

        create_usage(
            session,
            customer,
            sim,
            subscription,
            usage_date_value=date(2026, 4, 5),
            quantity=500.0,
            usage_type=UsageType.DATA,
        )

        create_usage(
            session,
            customer,
            sim,
            subscription,
            usage_date_value=date(2026, 4, 6),
            quantity=300.0,
            usage_type=UsageType.DATA,
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/data-consumption",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-04-01",
                "end_date": "2026-04-30",
                "customer_id": customer.id,
                "plan_id": plan.id,
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data
        assert data["total"] >= 1

        values = []

        for item in data["items"]:
            if "total_usage" in item:
                values.append(float(item["total_usage"]))
            elif "value" in item:
                values.append(float(item["value"]))

        if values:
            assert sum(values) > 0

    finally:
        session.close()


# ============================================================
# 5. NETWORK UPTIME
# ============================================================

def test_network_uptime_report():
    token = create_admin()

    session = SessionLocal()

    try:
        start = datetime(
            2026,
            5,
            1,
            0,
            0,
            tzinfo=timezone.utc,
        )

        resolution = start + timedelta(hours=1)

        create_outage(
            session,
            start_time=start,
            actual_resolution=resolution,
            severity=OutageSeverity.HIGH,
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/network-uptime",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-05-01",
                "end_date": "2026-05-02",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data
        assert data["total"] >= 1

        item = data["items"][0]

        uptime = item.get("uptime_percentage")

        if uptime is None:
            uptime = item.get("value")

        assert uptime is not None
        assert 0 <= float(uptime) <= 100

    finally:
        session.close()


# ============================================================
# 6. OUTAGE FREQUENCY
# ============================================================

def test_outage_frequency_report():
    token = create_admin()

    session = SessionLocal()

    try:
        create_outage(
            session,
            start_time=datetime(
                2026,
                6,
                5,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            actual_resolution=datetime(
                2026,
                6,
                5,
                11,
                0,
                tzinfo=timezone.utc,
            ),
            severity=OutageSeverity.HIGH,
            outage_type="Tower Failure",
        )

        create_outage(
            session,
            start_time=datetime(
                2026,
                6,
                10,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            actual_resolution=datetime(
                2026,
                6,
                10,
                10,
                30,
                tzinfo=timezone.utc,
            ),
            severity=OutageSeverity.MEDIUM,
            outage_type="Tower Failure",
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/outage-frequency",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-06-01",
                "end_date": "2026-06-30",
                "search": "Tower Failure",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data
        assert data["total"] >= 1

    finally:
        session.close()


# ============================================================
# 7. TICKET RESOLUTION
# ============================================================

def test_ticket_resolution_report():
    token = create_admin()

    session = SessionLocal()

    try:
        customer = create_customer(session)

        created_at = datetime(
            2026,
            7,
            5,
            9,
            0,
            tzinfo=timezone.utc,
        )

        resolved_at = created_at + timedelta(minutes=120)

        create_ticket(
            session,
            customer,
            created_at=created_at,
            resolved_at=resolved_at,
            status=TicketStatus.RESOLVED,
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/ticket-resolution",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-07-01",
                "end_date": "2026-07-31",
                "customer_id": customer.id,
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data
        assert data["total"] >= 1

    finally:
        session.close()


# ============================================================
# 8. SLA PERFORMANCE
# ============================================================

def test_sla_performance_report():
    token = create_admin()

    session = SessionLocal()

    try:
        customer = create_customer(session)

        sla_rule = create_sla_rule(session)

        start1 = datetime(
            2026,
            8,
            5,
            9,
            0,
            tzinfo=timezone.utc,
        )

        start2 = datetime(
            2026,
            8,
            6,
            9,
            0,
            tzinfo=timezone.utc,
        )

        ticket1 = create_ticket(
            session,
            customer,
            created_at=start1,
            resolved_at=start1 + timedelta(minutes=30),
            status=TicketStatus.RESOLVED,
        )

        ticket2 = create_ticket(
            session,
            customer,
            created_at=start2,
            resolved_at=start2 + timedelta(minutes=120),
            status=TicketStatus.RESOLVED,
        )

        create_ticket_sla(
            session,
            ticket1,
            sla_rule,
            start_time=start1,
            resolution_minutes=30,
            is_breached=False,
        )

        create_ticket_sla(
            session,
            ticket2,
            sla_rule,
            start_time=start2,
            resolution_minutes=120,
            is_breached=True,
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/sla-performance",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-08-01",
                "end_date": "2026-08-31",
                "customer_id": customer.id,
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data
        assert data["total"] >= 1

        item = data["items"][0]

        if "total_slas" in item:
            assert item["total_slas"] >= 1

        if "breached_slas" in item:
            assert item["breached_slas"] >= 1

    finally:
        session.close()


# ============================================================
# 9. TECHNICIAN PERFORMANCE
# ============================================================

def test_technician_performance_report():
    token = create_admin()

    session = SessionLocal()

    try:
        customer = create_customer(session)
        technician = create_technician(session)

        create_assignment(
            session,
            technician,
            customer,
            assigned_at=datetime(
                2026,
                9,
                5,
                9,
                0,
                tzinfo=timezone.utc,
            ),
            status=TechnicianJobStatus.COMPLETED,
        )

        create_assignment(
            session,
            technician,
            customer,
            assigned_at=datetime(
                2026,
                9,
                6,
                9,
                0,
                tzinfo=timezone.utc,
            ),
            status=TechnicianJobStatus.ASSIGNED,
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/technician-performance",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-09-01",
                "end_date": "2026-09-30",
                "customer_id": customer.id,
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data
        assert data["total"] >= 1

        item = data["items"][0]

        if "total_assignments" in item:
            assert item["total_assignments"] >= 1

    finally:
        session.close()


# ============================================================
# 10. CUSTOMER SERVICE
# ============================================================

def test_customer_service_report():
    token = create_admin()

    session = SessionLocal()

    try:
        customer = create_customer(session)

        user = session.get(
            User,
            customer.user_id,
        )

        create_service_request(
            session,
            customer,
            created_by=user.id,
            created_at=datetime(
                2026,
                9,
                10,
                9,
                0,
                tzinfo=timezone.utc,
            ),
            status=ServiceRequestStatus.COMPLETED,
        )

        create_service_request(
            session,
            customer,
            created_by=user.id,
            created_at=datetime(
                2026,
                9,
                11,
                9,
                0,
                tzinfo=timezone.utc,
            ),
            status=ServiceRequestStatus.PENDING,
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/customer-service",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-09-01",
                "end_date": "2026-09-30",
                "customer_id": customer.id,
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data
        assert data["total"] >= 1

    finally:
        session.close()


# ============================================================
# 11. PAGINATION
# ============================================================

def test_reports_pagination():
    token = create_admin()

    session = SessionLocal()

    try:
        for index in range(5):
            create_customer(
                session,
                created_at=datetime(
                    2026,
                    1,
                    index + 1,
                    tzinfo=timezone.utc,
                ),
            )

        session.commit()

        response = client.get(
            "/api/v1/reports/customer-growth",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "page": 1,
                "page_size": 2,
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) <= 2
        assert data["total"] >= 1

    finally:
        session.close()


# ============================================================
# 12. LOCATION FILTER
# ============================================================

def test_customer_growth_location_filter():
    token = create_admin()

    session = SessionLocal()

    try:
        create_customer(
            session,
            city="Tirupati",
            created_at=datetime(
                2026,
                1,
                5,
                tzinfo=timezone.utc,
            ),
        )

        create_customer(
            session,
            city="Chennai",
            state="Tamil Nadu",
            created_at=datetime(
                2026,
                1,
                10,
                tzinfo=timezone.utc,
            ),
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/customer-growth",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "location": "Tirupati",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data
        assert data["total"] >= 1

    finally:
        session.close()


# ============================================================
# 13. SEARCH FILTER
# ============================================================

def test_plan_popularity_search():
    token = create_admin()

    session = SessionLocal()

    try:
        customer = create_customer(session)

        plan = create_plan(
            session,
            plan_name="Searchable-Unlimited-Plan",
        )

        sim = create_sim(session, customer)

        create_subscription(
            session,
            customer,
            plan,
            sim,
            start_date_value=date(2026, 2, 1),
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/plan-popularity",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "search": "Searchable-Unlimited-Plan",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["total"] >= 1

    finally:
        session.close()


# ============================================================
# 14. AUTHENTICATION REQUIRED
# ============================================================

def test_reports_require_authentication():
    response = client.get(
        "/api/v1/reports/customer-growth"
    )

    assert response.status_code in [401, 403]


# ============================================================
# 15. SORT ORDER
# ============================================================

def test_customer_growth_sort_order():
    token = create_admin()

    session = SessionLocal()

    try:
        create_customer(
            session,
            created_at=datetime(
                2026,
                1,
                1,
                tzinfo=timezone.utc,
            ),
        )

        create_customer(
            session,
            created_at=datetime(
                2026,
                1,
                20,
                tzinfo=timezone.utc,
            ),
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/customer-growth",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "sort_order": "asc",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data

    finally:
        session.close()


# ============================================================
# 16. PLAN FILTER
# ============================================================

def test_data_consumption_plan_filter():
    token = create_admin()

    session = SessionLocal()

    try:
        customer = create_customer(session)

        plan1 = create_plan(
            session,
            plan_name="Data-Plan-One",
        )

        plan2 = create_plan(
            session,
            plan_name="Data-Plan-Two",
        )

        sim1 = create_sim(session, customer)
        sim2 = create_sim(session, customer)

        subscription1 = create_subscription(
            session,
            customer,
            plan1,
            sim1,
            start_date_value=date(2026, 3, 1),
        )

        subscription2 = create_subscription(
            session,
            customer,
            plan2,
            sim2,
            start_date_value=date(2026, 3, 1),
        )

        create_usage(
            session,
            customer,
            sim1,
            subscription1,
            usage_date_value=date(2026, 3, 5),
            quantity=1000,
        )

        create_usage(
            session,
            customer,
            sim2,
            subscription2,
            usage_date_value=date(2026, 3, 5),
            quantity=2000,
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/data-consumption",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-03-01",
                "end_date": "2026-03-31",
                "plan_id": plan1.id,
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data

    finally:
        session.close()


# ============================================================
# 17. CUSTOMER FILTER
# ============================================================

def test_subscription_trends_customer_filter():
    token = create_admin()

    session = SessionLocal()

    try:
        customer1 = create_customer(session)
        customer2 = create_customer(session)

        plan = create_plan(session)

        sim1 = create_sim(session, customer1)
        sim2 = create_sim(session, customer2)

        create_subscription(
            session,
            customer1,
            plan,
            sim1,
            start_date_value=date(2026, 4, 1),
        )

        create_subscription(
            session,
            customer2,
            plan,
            sim2,
            start_date_value=date(2026, 4, 2),
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/subscription-trends",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "customer_id": customer1.id,
                "start_date": "2026-04-01",
                "end_date": "2026-04-30",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert "items" in data

    finally:
        session.close()


# ============================================================
# 18. DATE RANGE FILTER
# ============================================================

def test_customer_growth_date_range_filter():
    token = create_admin()

    session = SessionLocal()

    try:
        create_customer(
            session,
            created_at=datetime(
                2026,
                1,
                5,
                tzinfo=timezone.utc,
            ),
        )

        create_customer(
            session,
            created_at=datetime(
                2026,
                3,
                5,
                tzinfo=timezone.utc,
            ),
        )

        session.commit()

        response = client.get(
            "/api/v1/reports/customer-growth",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["total"] >= 1

    finally:
        session.close()


# ============================================================
# 19. ALL REPORT ENDPOINTS EXIST
# ============================================================

def test_all_report_endpoints_are_registered():
    token = create_admin()

    endpoints = [
        "/api/v1/reports/customer-growth",
        "/api/v1/reports/subscription-trends",
        "/api/v1/reports/plan-popularity",
        "/api/v1/reports/data-consumption",
        "/api/v1/reports/network-uptime",
        "/api/v1/reports/outage-frequency",
        "/api/v1/reports/ticket-resolution",
        "/api/v1/reports/sla-performance",
        "/api/v1/reports/technician-performance",
        "/api/v1/reports/customer-service",
    ]

    for endpoint in endpoints:
        response = client.get(
            endpoint,
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code not in [404, 405], (
            f"{endpoint} is not registered: {response.text}"
        )