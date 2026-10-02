import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "telecom_service_network_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import text

from db.database import Base, SessionLocal, engine
from main import app

from tests.integration.test_support_tickets import (
    auth_headers,
    create_customer,
    create_customer_record,
    create_ticket,
    create_operations_manager,
    create_support_agent,
    login_user,
    register_user,
)


client = TestClient(app)


# ============================================================
# DATABASE SETUP
# ============================================================


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


# ============================================================
# HELPERS
# ============================================================


def unique_value(prefix="TEST"):
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def create_admin():
    data, payload = register_user(
        role="Super Admin",
        full_name=unique_value("Admin"),
    )

    token = login_user(
        payload["email"],
        payload["password"],
    )

    return {
        "user_id": data.get("id") or data.get("user_id"),
        "email": payload["email"],
        "password": payload["password"],
        "token": token,
        "data": data,
    }


def create_customer_with_record():
    customer = create_customer()

    customer_record = create_customer_record(
        customer
    )

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    return {
        "user": customer,
        "record": customer_record,
        "token": customer_token,
    }


def create_sla_rule(
    admin_token,
    rule_name=None,
    ticket_category="Network Issue",
    priority="Critical",
    customer_type=None,
    sla_minutes=60,
    warning_minutes=15,
    escalation_enabled=True,
):
    payload = {
        "rule_name": (
            rule_name
            or unique_value("SLA")
        ),
        "ticket_category": ticket_category,
        "priority": priority,
        "customer_type": customer_type,
        "sla_minutes": sla_minutes,
        "warning_minutes": warning_minutes,
        "escalation_enabled": escalation_enabled,
        "is_active": True,
    }

    response = client.post(
        "/api/v1/sla/rules",
        json=payload,
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_ticket_with_sla(
    customer_token,
    customer_record_id,
    category="Network Issue",
    priority="Critical",
):
    ticket = create_ticket(
        customer_record_id,
        customer_token,
        category=category,
        priority=priority,
    )

    return ticket


def get_ticket_sla_from_db(ticket_id):
    db = SessionLocal()

    try:
        row = db.execute(
            text(
                """
                SELECT
                    id,
                    ticket_id,
                    sla_rule_id,
                    start_time,
                    deadline,
                    resolution_time,
                    resolution_minutes,
                    status,
                    is_breached,
                    escalation_status,
                    escalated_at
                FROM ticket_slas
                WHERE ticket_id = :ticket_id
                """
            ),
            {
                "ticket_id": ticket_id,
            },
        ).mappings().first()

        return dict(row) if row else None

    finally:
        db.close()


def update_ticket_sla_deadline(
    ticket_id,
    deadline,
):
    db = SessionLocal()

    try:
        db.execute(
            text(
                """
                UPDATE ticket_slas
                SET deadline = :deadline
                WHERE ticket_id = :ticket_id
                """
            ),
            {
                "ticket_id": ticket_id,
                "deadline": deadline,
            },
        )

        db.commit()

    finally:
        db.close()


# ============================================================
# SLA RULE TESTS
# ============================================================


def test_create_sla_rule():
    admin = create_admin()

    rule = create_sla_rule(
        admin["token"],
        ticket_category="Network Issue",
        priority="Critical",
        sla_minutes=60,
        warning_minutes=15,
    )

    assert rule["id"] is not None
    assert rule["rule_name"]
    assert rule["ticket_category"] == "Network Issue"
    assert rule["priority"] == "Critical"
    assert rule["sla_minutes"] == 60
    assert rule["warning_minutes"] == 15
    assert rule["escalation_enabled"] is True
    assert rule["is_active"] is True


def test_create_sla_rule_with_customer_type():
    admin = create_admin()

    rule = create_sla_rule(
        admin["token"],
        ticket_category="Network Issue",
        priority="Critical",
        customer_type="Standard",
        sla_minutes=90,
        warning_minutes=20,
    )

    assert rule["customer_type"] == "Standard"
    assert rule["sla_minutes"] == 90


def test_duplicate_sla_rule_is_rejected():
    admin = create_admin()

    rule_name = unique_value("DUPLICATE")

    create_sla_rule(
        admin["token"],
        rule_name=rule_name,
    )

    response = client.post(
        "/api/v1/sla/rules",
        json={
            "rule_name": rule_name,
            "ticket_category": "Network Issue",
            "priority": "Critical",
            "customer_type": None,
            "sla_minutes": 60,
            "warning_minutes": 15,
            "escalation_enabled": True,
            "is_active": True,
        },
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "SLA rule with this name already exists"
    )


def test_get_sla_rules():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        priority="High",
        sla_minutes=120,
    )

    response = client.get(
        "/api/v1/sla/rules",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_active_sla_rules():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        rule_name=unique_value("ACTIVE"),
    )

    response = client.get(
        "/api/v1/sla/rules?is_active=true",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    for rule in response.json():
        assert rule["is_active"] is True


def test_get_sla_rule_by_id():
    admin = create_admin()

    rule = create_sla_rule(
        admin["token"]
    )

    response = client.get(
        f"/api/v1/sla/rules/{rule['id']}",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == rule["id"]
    assert data["rule_name"] == rule["rule_name"]


def test_update_sla_rule():
    admin = create_admin()

    rule = create_sla_rule(
        admin["token"],
        sla_minutes=60,
        warning_minutes=15,
    )

    response = client.put(
        f"/api/v1/sla/rules/{rule['id']}",
        json={
            "sla_minutes": 120,
            "warning_minutes": 30,
            "escalation_enabled": False,
        },
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sla_minutes"] == 120
    assert data["warning_minutes"] == 30
    assert data["escalation_enabled"] is False


def test_update_sla_rule_name():
    admin = create_admin()

    rule = create_sla_rule(
        admin["token"]
    )

    new_name = unique_value(
        "UPDATED-SLA"
    )

    response = client.put(
        f"/api/v1/sla/rules/{rule['id']}",
        json={
            "rule_name": new_name,
        },
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200
    assert (
        response.json()["rule_name"]
        == new_name
    )


def test_get_nonexistent_sla_rule():
    admin = create_admin()

    response = client.get(
        "/api/v1/sla/rules/999999",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 404


# ============================================================
# AUTOMATIC SLA CREATION
# ============================================================


def test_ticket_automatically_gets_sla():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        ticket_category="Network Issue",
        priority="Critical",
        sla_minutes=60,
        warning_minutes=15,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
        category="Network Issue",
        priority="Critical",
    )

    db_sla = get_ticket_sla_from_db(
        ticket["id"]
    )

    assert db_sla is not None
    assert db_sla["ticket_id"] == ticket["id"]


def test_sla_start_time_is_created():
    admin = create_admin()

    before = datetime.now(
        timezone.utc
    )

    create_sla_rule(
        admin["token"],
        ticket_category="Network Issue",
        priority="Critical",
        sla_minutes=60,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    after = datetime.now(
        timezone.utc
    )

    sla = get_ticket_sla_from_db(
        ticket["id"]
    )

    assert sla is not None
    assert sla["start_time"] is not None

    start_time = sla["start_time"]

    if start_time.tzinfo is None:
        start_time = start_time.replace(
            tzinfo=timezone.utc
        )

    assert (
        before - timedelta(seconds=2)
        <= start_time
        <= after + timedelta(seconds=2)
    )


def test_sla_deadline_is_calculated():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=60,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    sla = get_ticket_sla_from_db(
        ticket["id"]
    )

    assert sla is not None

    start_time = sla["start_time"]
    deadline = sla["deadline"]

    if start_time.tzinfo is None:
        start_time = start_time.replace(
            tzinfo=timezone.utc
        )

    if deadline.tzinfo is None:
        deadline = deadline.replace(
            tzinfo=timezone.utc
        )

    difference = (
        deadline - start_time
    ).total_seconds()

    assert difference == 60 * 60


# ============================================================
# TICKET SLA APIs
# ============================================================


def test_get_ticket_sla():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=60,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    response = client.get(
        f"/api/v1/sla/tickets/{ticket['id']}",
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ticket_id"] == ticket["id"]
    assert data["sla_rule_id"] is not None
    assert data["start_time"] is not None
    assert data["deadline"] is not None
    assert data["status"] == "Active"
    assert data["is_breached"] is False


def test_get_ticket_sla_status():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=60,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    response = client.get(
        f"/api/v1/sla/tickets/{ticket['id']}/status",
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ticket_id"] == ticket["id"]
    assert data["ticket_number"]
    assert data["sla_status"] == "Active"
    assert data["start_time"] is not None
    assert data["deadline"] is not None
    assert data["is_breached"] is False
    assert data["minutes_remaining"] is not None


def test_get_sla_for_nonexistent_ticket():
    admin = create_admin()

    response = client.get(
        "/api/v1/sla/tickets/999999",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 404


# ============================================================
# SLA RULE MATCHING
# ============================================================


def test_sla_matches_ticket_category_and_priority():
    admin = create_admin()

    rule = create_sla_rule(
        admin["token"],
        ticket_category="Network Issue",
        priority="Critical",
        sla_minutes=45,
        warning_minutes=10,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
        category="Network Issue",
        priority="Critical",
    )

    sla = get_ticket_sla_from_db(
        ticket["id"]
    )

    assert sla is not None
    assert sla["sla_rule_id"] == rule["id"]


def test_generic_sla_rule_matches_ticket():
    admin = create_admin()

    rule = create_sla_rule(
        admin["token"],
        ticket_category=None,
        priority=None,
        customer_type=None,
        sla_minutes=180,
        warning_minutes=30,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
        category="Device Issue",
        priority="Low",
    )

    sla = get_ticket_sla_from_db(
        ticket["id"]
    )

    assert sla is not None
    assert sla["sla_rule_id"] == rule["id"]


def test_more_specific_sla_rule_is_selected():
    admin = create_admin()

    generic_rule = create_sla_rule(
        admin["token"],
        rule_name=unique_value("GENERIC"),
        ticket_category=None,
        priority=None,
        customer_type=None,
        sla_minutes=240,
        warning_minutes=60,
    )

    specific_rule = create_sla_rule(
        admin["token"],
        rule_name=unique_value("SPECIFIC"),
        ticket_category="Network Issue",
        priority="Critical",
        customer_type=None,
        sla_minutes=30,
        warning_minutes=10,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
        category="Network Issue",
        priority="Critical",
    )

    sla = get_ticket_sla_from_db(
        ticket["id"]
    )

    assert sla is not None
    assert sla["sla_rule_id"] == specific_rule["id"]
    assert sla["sla_rule_id"] != generic_rule["id"]


# ============================================================
# SOON TO BREACH
# ============================================================


def test_soon_to_breach_tickets():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=60,
        warning_minutes=15,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    deadline = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    update_ticket_sla_deadline(
        ticket["id"],
        deadline,
    )

    response = client.get(
        "/api/v1/sla/soon-to-breach?minutes=60",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    ticket_ids = [
        item["ticket_id"]
        for item in data
    ]

    assert ticket["id"] in ticket_ids


def test_ticket_not_returned_when_deadline_is_far_away():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=240,
        warning_minutes=30,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    deadline = (
        datetime.now(timezone.utc)
        + timedelta(hours=5)
    )

    update_ticket_sla_deadline(
        ticket["id"],
        deadline,
    )

    response = client.get(
        "/api/v1/sla/soon-to-breach?minutes=60",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    ticket_ids = [
        item["ticket_id"]
        for item in response.json()
    ]

    assert ticket["id"] not in ticket_ids


def test_soon_to_breach_requires_positive_minutes():
    admin = create_admin()

    response = client.get(
        "/api/v1/sla/soon-to-breach?minutes=0",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 422


# ============================================================
# BREACHED TICKETS
# ============================================================


def test_breached_ticket_is_identified():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=60,
        warning_minutes=15,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    deadline = (
        datetime.now(timezone.utc)
        - timedelta(minutes=10)
    )

    update_ticket_sla_deadline(
        ticket["id"],
        deadline,
    )

    response = client.get(
        "/api/v1/sla/breached",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    ticket_ids = [
        item["ticket_id"]
        for item in data
    ]

    assert ticket["id"] in ticket_ids


def test_breached_ticket_is_marked_breached():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=60,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    deadline = (
        datetime.now(timezone.utc)
        - timedelta(minutes=5)
    )

    update_ticket_sla_deadline(
        ticket["id"],
        deadline,
    )

    response = client.get(
        "/api/v1/sla/breached",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    matching = [
        item
        for item in response.json()
        if item["ticket_id"] == ticket["id"]
    ]

    assert len(matching) == 1

    sla = matching[0]

    assert sla["status"] == "Breached"
    assert sla["is_breached"] is True
    assert (
        sla["escalation_status"]
        == "Escalated"
    )


def test_non_breached_ticket_not_returned():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=120,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    deadline = (
        datetime.now(timezone.utc)
        + timedelta(hours=2)
    )

    update_ticket_sla_deadline(
        ticket["id"],
        deadline,
    )

    response = client.get(
        "/api/v1/sla/breached",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    ticket_ids = [
        item["ticket_id"]
        for item in response.json()
    ]

    assert ticket["id"] not in ticket_ids


# ============================================================
# RESOLUTION / RESOLUTION TIME
# ============================================================


def test_resolve_ticket_sla():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=120,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    support_agent = create_support_agent()

    agent_token = login_user(
        support_agent["email"],
        support_agent["password"],
    )

    status_response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/status",
        json={
            "status": "Resolved",
            "resolution_notes": (
                "Network issue resolved"
            ),
        },
        headers=auth_headers(
            agent_token
        ),
    )

    assert status_response.status_code == 200

    response = client.post(
        f"/api/v1/sla/tickets/{ticket['id']}/resolve",
        headers=auth_headers(
            agent_token
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ticket_id"] == ticket["id"]
    assert data["status"] == "Resolved"
    assert data["resolution_time"] is not None
    assert data["resolution_minutes"] is not None
    assert data["resolution_minutes"] >= 0


def test_resolved_ticket_is_not_in_breached_list():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=120,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    support_agent = create_support_agent()

    agent_token = login_user(
        support_agent["email"],
        support_agent["password"],
    )

    status_response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/status",
        json={
            "status": "Resolved",
            "resolution_notes": "Resolved",
        },
        headers=auth_headers(
            agent_token
        ),
    )

    assert status_response.status_code == 200

    response = client.post(
        f"/api/v1/sla/tickets/{ticket['id']}/resolve",
        headers=auth_headers(
            agent_token
        ),
    )

    assert response.status_code == 200

    breached_response = client.get(
        "/api/v1/sla/breached",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert breached_response.status_code == 200

    ticket_ids = [
        item["ticket_id"]
        for item in breached_response.json()
    ]

    assert ticket["id"] not in ticket_ids


# ============================================================
# BREACH AFTER RESOLUTION
# ============================================================


def test_resolution_after_deadline_is_marked_breached():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=60,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    deadline = (
        datetime.now(timezone.utc)
        - timedelta(minutes=10)
    )

    update_ticket_sla_deadline(
        ticket["id"],
        deadline,
    )

    support_agent = create_support_agent()

    agent_token = login_user(
        support_agent["email"],
        support_agent["password"],
    )

    status_response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/status",
        json={
            "status": "Resolved",
            "resolution_notes": (
                "Resolved after SLA deadline"
            ),
        },
        headers=auth_headers(
            agent_token
        ),
    )

    assert status_response.status_code == 200

    response = client.post(
        f"/api/v1/sla/tickets/{ticket['id']}/resolve",
        headers=auth_headers(
            agent_token
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Resolved"
    assert data["is_breached"] is True
    assert (
        data["escalation_status"]
        == "Escalated"
    )


# ============================================================
# WARNING / ESCALATION
# ============================================================


def test_sla_warning_status_when_deadline_is_near():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=60,
        warning_minutes=30,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    deadline = (
        datetime.now(timezone.utc)
        + timedelta(minutes=15)
    )

    update_ticket_sla_deadline(
        ticket["id"],
        deadline,
    )

    response = client.get(
        f"/api/v1/sla/tickets/{ticket['id']}/status",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["escalation_status"]
        == "Warning"
    )
    assert data["is_breached"] is False


# ============================================================
# RBAC
# ============================================================


def test_customer_cannot_create_sla_rule():
    customer = create_customer()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    response = client.post(
        "/api/v1/sla/rules",
        json={
            "rule_name": unique_value("CUSTOMER"),
            "ticket_category": "Network Issue",
            "priority": "Critical",
            "customer_type": None,
            "sla_minutes": 60,
            "warning_minutes": 15,
            "escalation_enabled": True,
            "is_active": True,
        },
        headers=auth_headers(
            customer_token
        ),
    )

    assert response.status_code == 403


def test_support_agent_cannot_create_sla_rule():
    support_agent = create_support_agent()

    token = login_user(
        support_agent["email"],
        support_agent["password"],
    )

    response = client.post(
        "/api/v1/sla/rules",
        json={
            "rule_name": unique_value("AGENT"),
            "ticket_category": "Network Issue",
            "priority": "Critical",
            "customer_type": None,
            "sla_minutes": 60,
            "warning_minutes": 15,
            "escalation_enabled": True,
            "is_active": True,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_operations_manager_can_create_sla_rule():
    operations = create_operations_manager()

    token = login_user(
        operations["email"],
        operations["password"],
    )

    response = client.post(
        "/api/v1/sla/rules",
        json={
            "rule_name": unique_value("OPS"),
            "ticket_category": "Network Issue",
            "priority": "High",
            "customer_type": None,
            "sla_minutes": 120,
            "warning_minutes": 30,
            "escalation_enabled": True,
            "is_active": True,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201


def test_customer_can_view_sla():
    admin = create_admin()

    create_sla_rule(
        admin["token"],
        sla_minutes=60,
    )

    customer = create_customer_with_record()

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
    )

    response = client.get(
        f"/api/v1/sla/tickets/{ticket['id']}",
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert response.status_code == 200


# ============================================================
# VALIDATION
# ============================================================


def test_sla_rule_rejects_zero_sla_minutes():
    admin = create_admin()

    response = client.post(
        "/api/v1/sla/rules",
        json={
            "rule_name": unique_value("INVALID"),
            "ticket_category": "Network Issue",
            "priority": "Critical",
            "customer_type": None,
            "sla_minutes": 0,
            "warning_minutes": 15,
            "escalation_enabled": True,
            "is_active": True,
        },
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 422


def test_sla_rule_rejects_negative_warning_minutes():
    admin = create_admin()

    response = client.post(
        "/api/v1/sla/rules",
        json={
            "rule_name": unique_value("INVALID"),
            "ticket_category": "Network Issue",
            "priority": "Critical",
            "customer_type": None,
            "sla_minutes": 60,
            "warning_minutes": -1,
            "escalation_enabled": True,
            "is_active": True,
        },
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 422


# ============================================================
# FULL SLA WORKFLOW
# ============================================================


def test_complete_sla_workflow():
    # --------------------------------------------------------
    # 1. Admin
    # --------------------------------------------------------

    admin = create_admin()

    # --------------------------------------------------------
    # 2. Create SLA Rule
    # --------------------------------------------------------

    rule = create_sla_rule(
        admin["token"],
        rule_name=unique_value(
            "FULL-WORKFLOW"
        ),
        ticket_category="Network Issue",
        priority="Critical",
        sla_minutes=60,
        warning_minutes=15,
    )

    assert rule["id"] is not None

    # --------------------------------------------------------
    # 3. Customer
    # --------------------------------------------------------

    customer = create_customer_with_record()

    # --------------------------------------------------------
    # 4. Create Ticket
    # --------------------------------------------------------

    ticket = create_ticket_with_sla(
        customer["token"],
        customer["record"]["id"],
        category="Network Issue",
        priority="Critical",
    )

    assert ticket["id"] is not None

    # --------------------------------------------------------
    # 5. Verify SLA Created
    # --------------------------------------------------------

    sla = get_ticket_sla_from_db(
        ticket["id"]
    )

    assert sla is not None
    assert sla["sla_rule_id"] == rule["id"]
    assert sla["status"] == "Active"
    assert sla["is_breached"] is False

    # --------------------------------------------------------
    # 6. Verify Status API
    # --------------------------------------------------------

    status_response = client.get(
        f"/api/v1/sla/tickets/{ticket['id']}/status",
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert status_response.status_code == 200

    status_data = status_response.json()

    assert status_data["ticket_id"] == ticket["id"]
    assert status_data["sla_status"] == "Active"
    assert (
        status_data["minutes_remaining"]
        is not None
    )

    # --------------------------------------------------------
    # 7. Move Ticket Near Deadline
    # --------------------------------------------------------

    deadline = (
        datetime.now(timezone.utc)
        + timedelta(minutes=10)
    )

    update_ticket_sla_deadline(
        ticket["id"],
        deadline,
    )

    # --------------------------------------------------------
    # 8. Soon-to-Breach API
    # --------------------------------------------------------

    soon_response = client.get(
        "/api/v1/sla/soon-to-breach?minutes=30",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert soon_response.status_code == 200

    soon_ids = [
        item["ticket_id"]
        for item in soon_response.json()
    ]

    assert ticket["id"] in soon_ids

    # --------------------------------------------------------
    # 9. Force Breach
    # --------------------------------------------------------

    breached_deadline = (
        datetime.now(timezone.utc)
        - timedelta(minutes=5)
    )

    update_ticket_sla_deadline(
        ticket["id"],
        breached_deadline,
    )

    # --------------------------------------------------------
    # 10. Breached API
    # --------------------------------------------------------

    breached_response = client.get(
        "/api/v1/sla/breached",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert breached_response.status_code == 200

    breached_items = [
        item
        for item in breached_response.json()
        if item["ticket_id"] == ticket["id"]
    ]

    assert len(breached_items) == 1

    breached_sla = breached_items[0]

    assert (
        breached_sla["status"]
        == "Breached"
    )

    assert (
        breached_sla["is_breached"]
        is True
    )

    assert (
        breached_sla["escalation_status"]
        == "Escalated"
    )