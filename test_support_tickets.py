import os
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "telecom_service_network_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import text

from db.database import Base, SessionLocal, engine
from main import app


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

def unique_value(prefix="test"):
    return f"{prefix}_{uuid4().hex[:8]}"


def register_user(
    role="Customer",
    email=None,
    full_name=None,
):
    if email is None:
        email = f"{unique_value('user')}@example.com"

    payload = {
        "full_name": full_name or unique_value("User"),
        "email": email,
        "phone": f"9{uuid4().int % 1000000000:09d}",
        "password": "Test@12345",
        "role": role,
    }

    response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert response.status_code in [200, 201], response.text

    return response.json(), payload


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

    token = (
        data.get("access_token")
        or data.get("token")
    )

    assert token is not None, data

    return token


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def get_user_id(response_data):
    return (
        response_data.get("id")
        or response_data.get("user_id")
        or response_data.get("user", {}).get("id")
    )


def create_customer():
    data, payload = register_user(
        role="Customer",
        full_name=unique_value("Customer"),
    )

    user_id = get_user_id(data)

    assert user_id is not None, data

    return {
        "user_id": user_id,
        "email": payload["email"],
        "password": payload["password"],
        "data": data,
    }


def create_support_agent():
    data, payload = register_user(
        role="Support Agent",
        full_name=unique_value("SupportAgent"),
    )

    user_id = get_user_id(data)

    assert user_id is not None, data

    return {
        "user_id": user_id,
        "email": payload["email"],
        "password": payload["password"],
        "data": data,
    }


def create_operations_manager():
    data, payload = register_user(
        role="Operations Manager",
        full_name=unique_value("Operations"),
    )

    user_id = get_user_id(data)

    assert user_id is not None, data

    return {
        "user_id": user_id,
        "email": payload["email"],
        "password": payload["password"],
        "data": data,
    }


def create_network_engineer():
    data, payload = register_user(
        role="Network Engineer",
        full_name=unique_value("Engineer"),
    )

    user_id = get_user_id(data)

    assert user_id is not None, data

    return {
        "user_id": user_id,
        "email": payload["email"],
        "password": payload["password"],
        "data": data,
    }


def create_field_technician():
    data, payload = register_user(
        role="Field Technician",
        full_name=unique_value("Technician"),
    )

    user_id = get_user_id(data)

    assert user_id is not None, data

    # Technician records require an elevated role.
    admin_data, admin_payload = register_user(
        role="Super Admin",
        full_name=unique_value("Admin"),
    )

    admin_token = login_user(
        admin_payload["email"],
        admin_payload["password"],
    )

    technician_payload = {
        "user_id": user_id,
        "employee_id": unique_value("EMP"),
        "full_name": payload["full_name"],
        "phone": payload["phone"],
        "availability": "Available",
        "service_area": "Tirupati",
        "address": "Test Address",
    }

    response = client.post(
        "/api/v1/technicians/",
        json=technician_payload,
        headers=auth_headers(admin_token),
    )

    assert response.status_code in [200, 201], response.text

    technician = response.json()

    return {
        "user_id": user_id,
        "technician_id": technician["id"],
        "email": payload["email"],
        "password": payload["password"],
        "data": technician,
    }


def create_customer_record(customer):
    """
    Creates the telecom customer record using
    a Super Admin because the customer creation
    endpoint requires elevated permissions.
    """

    admin_data, admin_payload = register_user(
        role="Super Admin",
        full_name=unique_value("Admin"),
    )

    admin_token = login_user(
        admin_payload["email"],
        admin_payload["password"],
    )

    payload = {
        "user_id": customer["user_id"],
        "customer_number": unique_value("CUST"),
        "full_name": unique_value("Customer"),
        "phone": f"9{uuid4().int % 1000000000:09d}",
        "address": "Test Address",
    }

    response = client.post(
        "/api/v1/customers/",
        json=payload,
        headers=auth_headers(admin_token),
    )

    assert response.status_code in [200, 201], response.text

    data = response.json()

    return {
        "id": data["id"],
        "user_id": customer["user_id"],
        "email": customer["email"],
        "password": customer["password"],
        "data": data,
    }

def create_ticket(
    customer_id,
    token,
    category="Network Issue",
    priority="Medium",
):
    payload = {
        "customer_id": customer_id,
        "category": category,
        "subject": unique_value("Network Problem"),
        "description": "Customer is experiencing a network connectivity problem.",
        "priority": priority,
    }

    response = client.post(
        "/api/v1/support-tickets/",
        json=payload,
        headers=auth_headers(token),
    )

    assert response.status_code in [200, 201], response.text

    return response.json()


# ============================================================
# LEVEL 12 - CREATE TICKET
# ============================================================

def test_create_network_issue_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_id=customer_record["id"],
        token=token,
        category="Network Issue",
    )

    assert ticket["id"] is not None
    assert ticket["ticket_number"].startswith("TKT-")
    assert ticket["customer_id"] == customer_record["id"]
    assert ticket["category"] == "Network Issue"
    assert ticket["status"] == "Open"
    assert ticket["priority"] == "Medium"


def test_create_sim_issue_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_id=customer_record["id"],
        token=token,
        category="SIM Issue",
    )

    assert ticket["category"] == "SIM Issue"
    assert ticket["status"] == "Open"


def test_create_data_issue_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_id=customer_record["id"],
        token=token,
        category="Data Issue",
    )

    assert ticket["category"] == "Data Issue"


def test_create_voice_issue_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_id=customer_record["id"],
        token=token,
        category="Voice Issue",
    )

    assert ticket["category"] == "Voice Issue"


def test_create_device_issue_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_id=customer_record["id"],
        token=token,
        category="Device Issue",
    )

    assert ticket["category"] == "Device Issue"


def test_create_account_issue_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_id=customer_record["id"],
        token=token,
        category="Account Issue",
    )

    assert ticket["category"] == "Account Issue"


def test_create_service_request_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_id=customer_record["id"],
        token=token,
        category="Service Request",
    )

    assert ticket["category"] == "Service Request"


# ============================================================
# LEVEL 12 - PRIORITY
# ============================================================

def test_create_high_priority_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        token,
        priority="High",
    )

    assert ticket["priority"] == "High"


def test_create_critical_priority_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        token,
        priority="Critical",
    )

    assert ticket["priority"] == "Critical"


# ============================================================
# LEVEL 12 - GET TICKETS
# ============================================================

def test_get_ticket_by_id():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        token,
    )

    response = client.get(
        f"/api/v1/support-tickets/{ticket['id']}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == ticket["id"]
    assert data["ticket_number"] == ticket["ticket_number"]


def test_get_all_tickets():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    create_ticket(
        customer_record["id"],
        token,
    )

    response = client.get(
        "/api/v1/support-tickets/",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_filter_tickets_by_customer():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    create_ticket(
        customer_record["id"],
        token,
    )

    response = client.get(
        "/api/v1/support-tickets/",
        params={
            "customer_id": customer_record["id"],
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) >= 1

    for ticket in data:
        assert ticket["customer_id"] == customer_record["id"]


def test_filter_tickets_by_status():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    create_ticket(
        customer_record["id"],
        token,
    )

    response = client.get(
        "/api/v1/support-tickets/",
        params={
            "ticket_status": "Open",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    for ticket in data:
        assert ticket["status"] == "Open"


# ============================================================
# LEVEL 12 - UPDATE TICKET
# ============================================================

def test_update_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.put(
        f"/api/v1/support-tickets/{ticket['id']}",
        json={
            "subject": "Updated Network Problem",
            "description": "Updated ticket description.",
            "priority": "High",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["subject"] == "Updated Network Problem"
    assert data["priority"] == "High"


# ============================================================
# LEVEL 13 - AGENT ASSIGNMENT
# ============================================================

def test_assign_ticket_to_support_agent():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()
    operations = create_operations_manager()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    operations_token = login_user(
        operations["email"],
        operations["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/assign-agent",
        json={
            "agent_id": agent["user_id"],
        },
        headers=auth_headers(operations_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["assigned_agent_id"] == agent["user_id"]
    assert data["status"] == "Assigned"


# ============================================================
# LEVEL 13 - TECHNICIAN ASSIGNMENT
# ============================================================

def test_assign_ticket_to_technician():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    technician = create_field_technician()
    operations = create_operations_manager()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    operations_token = login_user(
        operations["email"],
        operations["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/assign-technician",
        json={
            "technician_id": technician["technician_id"],
        },
        headers=auth_headers(operations_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["assigned_technician_id"] == technician["technician_id"]
    assert data["status"] == "Assigned"


# ============================================================
# LEVEL 13 - REASSIGN AGENT
# ============================================================

def test_reassign_ticket_to_another_agent():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent1 = create_support_agent()
    agent2 = create_support_agent()
    operations = create_operations_manager()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    operations_token = login_user(
        operations["email"],
        operations["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/assign-agent",
        json={
            "agent_id": agent1["user_id"],
        },
        headers=auth_headers(operations_token),
    )

    assert response.status_code == 200, response.text

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/reassign",
        json={
            "agent_id": agent2["user_id"],
        },
        headers=auth_headers(operations_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["assigned_agent_id"] == agent2["user_id"]


# ============================================================
# LEVEL 13 - STATUS
# ============================================================

def test_update_ticket_to_in_progress():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/status",
        json={
            "status": "In Progress",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["status"] == "In Progress"


def test_resolve_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/status",
        json={
            "status": "Resolved",
            "resolution_notes": "Network issue resolved successfully.",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["status"] == "Resolved"
    assert data["resolution_notes"] == "Network issue resolved successfully."
    assert data["resolved_at"] is not None


def test_close_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/status",
        json={
            "status": "Closed",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["status"] == "Closed"
    assert data["closed_at"] is not None


def test_waiting_for_customer_status():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/status",
        json={
            "status": "Waiting for Customer",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    assert response.json()["status"] == "Waiting for Customer"


# ============================================================
# LEVEL 13 - ESCALATION
# ============================================================

def test_escalate_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/escalate",
        json={
            "escalation_level": 2,
            "reason": "Issue requires higher-level support.",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["escalation_level"] == 2
    assert data["is_escalated"] is True


def test_escalate_ticket_to_level_five():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/escalate",
        json={
            "escalation_level": 5,
            "reason": "Critical network issue.",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["escalation_level"] == 5
    assert data["is_escalated"] is True


# ============================================================
# LEVEL 13 - INTERNAL COMMENTS
# ============================================================

def test_add_internal_comment():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.post(
        f"/api/v1/support-tickets/{ticket['id']}/comments",
        json={
            "comment": "Customer contacted. Network team is investigating.",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code in [200, 201], response.text

    data = response.json()

    assert data["ticket_id"] == ticket["id"]
    assert data["author_id"] == agent["user_id"]
    assert data["comment"] == (
        "Customer contacted. Network team is investigating."
    )


def test_get_ticket_comments():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    client.post(
        f"/api/v1/support-tickets/{ticket['id']}/comments",
        json={
            "comment": "Internal investigation started.",
        },
        headers=auth_headers(agent_token),
    )

    response = client.get(
        f"/api/v1/support-tickets/{ticket['id']}/comments",
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert data[0]["ticket_id"] == ticket["id"]


# ============================================================
# LEVEL 13 - TICKET HISTORY
# ============================================================

def test_ticket_history_contains_created_action():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        token,
    )

    response = client.get(
        f"/api/v1/support-tickets/{ticket['id']}/history",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    actions = [item["action"] for item in data]

    assert "Created" in actions


def test_ticket_history_after_assignment():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()
    operations = create_operations_manager()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    operations_token = login_user(
        operations["email"],
        operations["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/assign-agent",
        json={
            "agent_id": agent["user_id"],
        },
        headers=auth_headers(operations_token),
    )

    assert response.status_code == 200, response.text

    response = client.get(
        f"/api/v1/support-tickets/{ticket['id']}/history",
        headers=auth_headers(operations_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    actions = [item["action"] for item in data]

    assert "Created" in actions
    assert "Assigned" in actions


def test_ticket_history_after_status_change():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/status",
        json={
            "status": "In Progress",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    response = client.get(
        f"/api/v1/support-tickets/{ticket['id']}/history",
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    actions = [item["action"] for item in data]

    assert "Created" in actions
    assert "Status Changed" in actions


def test_ticket_history_after_escalation():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/escalate",
        json={
            "escalation_level": 3,
            "reason": "Requires network engineering support.",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    response = client.get(
        f"/api/v1/support-tickets/{ticket['id']}/history",
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    actions = [item["action"] for item in data]

    assert "Escalated" in actions


# ============================================================
# LEVEL 13 - AUTHORIZATION
# ============================================================

def test_customer_cannot_assign_agent():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/assign-agent",
        json={
            "agent_id": agent["user_id"],
        },
        headers=auth_headers(customer_token),
    )

    assert response.status_code == 403


def test_customer_cannot_escalate_ticket():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/escalate",
        json={
            "escalation_level": 2,
            "reason": "Test escalation.",
        },
        headers=auth_headers(customer_token),
    )

    assert response.status_code == 403


def test_customer_cannot_add_internal_comment():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.post(
        f"/api/v1/support-tickets/{ticket['id']}/comments",
        json={
            "comment": "Customer trying to add internal comment.",
        },
        headers=auth_headers(customer_token),
    )

    assert response.status_code == 403


# ============================================================
# VALIDATION TESTS
# ============================================================

def test_invalid_ticket_category():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    response = client.post(
        "/api/v1/support-tickets/",
        json={
            "customer_id": customer_record["id"],
            "category": "Invalid Category",
            "subject": "Test ticket",
            "description": "This is a test ticket.",
            "priority": "Medium",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_invalid_ticket_priority():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    token = login_user(
        customer["email"],
        customer["password"],
    )

    response = client.post(
        "/api/v1/support-tickets/",
        json={
            "customer_id": customer_record["id"],
            "category": "Network Issue",
            "subject": "Test ticket",
            "description": "This is a test ticket.",
            "priority": "Invalid",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_invalid_ticket_status():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/status",
        json={
            "status": "Invalid Status",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 422


def test_escalation_level_cannot_be_zero():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    ticket = create_ticket(
        customer_record["id"],
        customer_token,
    )

    response = client.patch(
        f"/api/v1/support-tickets/{ticket['id']}/escalate",
        json={
            "escalation_level": 0,
            "reason": "Invalid escalation.",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 422


# ============================================================
# NOT FOUND TESTS
# ============================================================

def test_get_nonexistent_ticket():
    customer = create_customer()

    token = login_user(
        customer["email"],
        customer["password"],
    )

    response = client.get(
        "/api/v1/support-tickets/999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_update_nonexistent_ticket():
    agent = create_support_agent()

    token = login_user(
        agent["email"],
        agent["password"],
    )

    response = client.put(
        "/api/v1/support-tickets/999999",
        json={
            "subject": "Updated",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_assign_nonexistent_ticket():
    operations = create_operations_manager()
    agent = create_support_agent()

    operations_token = login_user(
        operations["email"],
        operations["password"],
    )

    response = client.patch(
        "/api/v1/support-tickets/999999/assign-agent",
        json={
            "agent_id": agent["user_id"],
        },
        headers=auth_headers(operations_token),
    )

    assert response.status_code == 404


# ============================================================
# COMPLETE WORKFLOW
# ============================================================

def test_complete_support_ticket_workflow():
    customer = create_customer()
    customer_record = create_customer_record(customer)

    agent = create_support_agent()
    technician = create_field_technician()
    operations = create_operations_manager()

    customer_token = login_user(
        customer["email"],
        customer["password"],
    )

    agent_token = login_user(
        agent["email"],
        agent["password"],
    )

    operations_token = login_user(
        operations["email"],
        operations["password"],
    )

    # 1. Customer creates ticket
    ticket = create_ticket(
        customer_record["id"],
        customer_token,
        category="Network Issue",
        priority="High",
    )

    assert ticket["status"] == "Open"

    ticket_id = ticket["id"]

    # 2. Assign support agent
    response = client.patch(
        f"/api/v1/support-tickets/{ticket_id}/assign-agent",
        json={
            "agent_id": agent["user_id"],
        },
        headers=auth_headers(operations_token),
    )

    assert response.status_code == 200, response.text

    ticket = response.json()

    assert ticket["assigned_agent_id"] == agent["user_id"]
    assert ticket["status"] == "Assigned"

    # 3. Assign technician
    response = client.patch(
        f"/api/v1/support-tickets/{ticket_id}/assign-technician",
        json={
            "technician_id": technician["technician_id"],
        },
        headers=auth_headers(operations_token),
    )

    assert response.status_code == 200, response.text

    ticket = response.json()

    assert ticket["assigned_technician_id"] == technician["technician_id"]

    # 4. Move to In Progress
    response = client.patch(
        f"/api/v1/support-tickets/{ticket_id}/status",
        json={
            "status": "In Progress",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "In Progress"

    # 5. Add internal comment
    response = client.post(
        f"/api/v1/support-tickets/{ticket_id}/comments",
        json={
            "comment": "Technician is investigating the network issue.",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code in [200, 201], response.text

    # 6. Escalate
    response = client.patch(
        f"/api/v1/support-tickets/{ticket_id}/escalate",
        json={
            "escalation_level": 2,
            "reason": "Requires network engineering review.",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    ticket = response.json()

    assert ticket["is_escalated"] is True
    assert ticket["escalation_level"] == 2

    # 7. Resolve
    response = client.patch(
        f"/api/v1/support-tickets/{ticket_id}/status",
        json={
            "status": "Resolved",
            "resolution_notes": "Network service restored.",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    ticket = response.json()

    assert ticket["status"] == "Resolved"
    assert ticket["resolved_at"] is not None
    assert ticket["resolution_notes"] == "Network service restored."

    # 8. Close
    response = client.patch(
        f"/api/v1/support-tickets/{ticket_id}/status",
        json={
            "status": "Closed",
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    ticket = response.json()

    assert ticket["status"] == "Closed"
    assert ticket["closed_at"] is not None

    # 9. Verify comments
    response = client.get(
        f"/api/v1/support-tickets/{ticket_id}/comments",
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    comments = response.json()

    assert len(comments) >= 1

    # 10. Verify history
    response = client.get(
        f"/api/v1/support-tickets/{ticket_id}/history",
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200, response.text

    history = response.json()

    assert len(history) >= 5

    actions = [item["action"] for item in history]

    assert "Created" in actions
    assert "Assigned" in actions
    assert "Status Changed" in actions
    assert "Escalated" in actions
    assert "Comment Added" in actions