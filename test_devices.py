import os
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "telecom_service_network_test"
)

from fastapi.testclient import TestClient

from db.database import Base, engine
from main import app


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# =========================================================
# HELPERS
# =========================================================

def unique_email(prefix="user"):
    safe_prefix = prefix.lower().replace(" ", "_")
    return f"{safe_prefix}_{uuid4().hex[:8]}@example.com"


def register_user(role="Customer", email=None):

    if email is None:
        email = unique_email(role)

    role_map = {
        "SUPER_ADMIN": "Super Admin",
        "OPERATIONS_MANAGER": "Operations Manager",
        "SUPPORT_AGENT": "Support Agent",
        "NETWORK_ENGINEER": "Network Engineer",
        "FIELD_TECHNICIAN": "Field Technician",
        "CUSTOMER": "Customer",
    }

    api_role = role_map.get(role, role)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": email,
            "phone": "9876543210",
            "password": "Test@12345",
            "role": api_role,
        },
    )

    assert response.status_code in (200, 201), response.text

    return response.json()


def login_user(
    email,
    password="Test@12345",
):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def create_admin():

    email = unique_email("admin")

    register_user(
        role="SUPER_ADMIN",
        email=email,
    )

    return login_user(email)


def create_customer(admin_token):

    email = unique_email("customer")

    user = register_user(
        role="CUSTOMER",
        email=email,
    )

    response = client.post(
        "/api/v1/customers",
        headers=auth_headers(admin_token),
        json={
            "user_id": user["id"],
            "customer_number": (
                f"CUST-{uuid4().hex[:8].upper()}"
            ),
            "address_line1": "Test Street",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "postal_code": "517501",
            "kyc_status": "Verified",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_plan(admin_token):

    response = client.post(
        "/api/v1/plans",
        headers=auth_headers(admin_token),
        json={
            "plan_name": (
                f"Device Plan {uuid4().hex[:8]}"
            ),
            "description": "Test device plan",
            "plan_type": "Prepaid",
            "validity_days": 30,
            "data_limit_mb": 10000,
            "voice_limit_minutes": 1000,
            "sms_limit": 1000,
            "price": 499,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_sim(
    admin_token,
    customer_id=None,
    plan_id=None,
    sim_number=None,
):

    if sim_number is None:
        sim_number = (
            f"SIM-{uuid4().hex[:10].upper()}"
        )

    payload = {
        "sim_number": sim_number,
        "sim_type": "Physical",
    }

    if customer_id is not None:
        payload["customer_id"] = customer_id

    if plan_id is not None:
        payload["plan_id"] = plan_id

    response = client.post(
        "/api/v1/sims",
        headers=auth_headers(admin_token),
        json=payload,
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_device(
    admin_token,
    customer_id=None,
    imei=None,
):

    if imei is None:
        imei = (
            "35"
            + uuid4().hex[:13]
        )

    payload = {
        "imei": imei,
        "model": "Galaxy Test",
        "manufacturer": "Samsung",
        "device_type": "Smartphone",
    }

    if customer_id is not None:
        payload["customer_id"] = customer_id

    response = client.post(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        json=payload,
    )

    assert response.status_code == 201, response.text

    return response.json()


# =========================================================
# CREATE DEVICE
# =========================================================

def test_create_device_without_customer():

    admin_token = create_admin()

    response = client.post(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        json={
            "imei": "351234567890123",
            "model": "Galaxy S25",
            "manufacturer": "Samsung",
            "device_type": "Smartphone",
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["imei"] == "351234567890123"
    assert data["model"] == "Galaxy S25"
    assert data["manufacturer"] == "Samsung"
    assert data["device_type"] == "Smartphone"
    assert data["status"] == "Active"
    assert data["customer_id"] is None


def test_create_device_with_customer():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    device = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    assert device["customer_id"] == customer["id"]
    assert device["status"] == "Active"


def test_create_tablet():

    admin_token = create_admin()

    response = client.post(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        json={
            "imei": "351111111111111",
            "model": "Test Tablet",
            "manufacturer": "Apple",
            "device_type": "Tablet",
        },
    )

    assert response.status_code == 201

    assert (
        response.json()["device_type"]
        == "Tablet"
    )


def test_create_router():

    admin_token = create_admin()

    response = client.post(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        json={
            "imei": "352222222222222",
            "model": "Test Router",
            "manufacturer": "TP-Link",
            "device_type": "Router",
        },
    )

    assert response.status_code == 201

    assert (
        response.json()["device_type"]
        == "Router"
    )


def test_create_modem():

    admin_token = create_admin()

    response = client.post(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        json={
            "imei": "353333333333333",
            "model": "Test Modem",
            "manufacturer": "Huawei",
            "device_type": "Modem",
        },
    )

    assert response.status_code == 201

    assert (
        response.json()["device_type"]
        == "Modem"
    )


# =========================================================
# DUPLICATE IMEI
# =========================================================

def test_duplicate_imei_is_rejected():

    admin_token = create_admin()

    imei = "354444444444444"

    first = client.post(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        json={
            "imei": imei,
            "model": "Device One",
            "manufacturer": "Samsung",
            "device_type": "Smartphone",
        },
    )

    assert first.status_code == 201

    second = client.post(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        json={
            "imei": imei,
            "model": "Device Two",
            "manufacturer": "Apple",
            "device_type": "Smartphone",
        },
    )

    assert second.status_code == 409
    assert "IMEI" in second.json()["detail"]


def test_duplicate_imei_on_update_is_rejected():

    admin_token = create_admin()

    device_one = create_device(
        admin_token
    )

    device_two = create_device(
        admin_token
    )

    response = client.patch(
        f"/api/v1/devices/{device_two['id']}",
        headers=auth_headers(admin_token),
        json={
            "imei": device_one["imei"],
        },
    )

    assert response.status_code == 409
    assert "IMEI" in response.json()["detail"]


# =========================================================
# CUSTOMER VALIDATION
# =========================================================

def test_device_with_invalid_customer_is_rejected():

    admin_token = create_admin()

    response = client.post(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        json={
            "imei": "355555555555555",
            "model": "Test Phone",
            "manufacturer": "Samsung",
            "device_type": "Smartphone",
            "customer_id": 999999,
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Customer not found"
    )


# =========================================================
# GET
# =========================================================

def test_get_device():

    admin_token = create_admin()

    device = create_device(
        admin_token
    )

    response = client.get(
        f"/api/v1/devices/{device['id']}",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == device["id"]
    assert data["imei"] == device["imei"]


def test_get_nonexistent_device():

    admin_token = create_admin()

    response = client.get(
        "/api/v1/devices/999999",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Device not found"
    )


# =========================================================
# UPDATE
# =========================================================

def test_update_device():

    admin_token = create_admin()

    device = create_device(
        admin_token
    )

    response = client.patch(
        f"/api/v1/devices/{device['id']}",
        headers=auth_headers(admin_token),
        json={
            "model": "Updated Galaxy",
            "manufacturer": "Updated Samsung",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["model"] == "Updated Galaxy"
    assert (
        data["manufacturer"]
        == "Updated Samsung"
    )


def test_assign_customer_to_existing_device():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    device = create_device(
        admin_token
    )

    response = client.patch(
        f"/api/v1/devices/{device['id']}",
        headers=auth_headers(admin_token),
        json={
            "customer_id": customer["id"],
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["customer_id"]
        == customer["id"]
    )


# =========================================================
# DEVICE STATUS
# =========================================================

def test_deactivate_device():

    admin_token = create_admin()

    device = create_device(
        admin_token
    )

    response = client.patch(
        f"/api/v1/devices/{device['id']}/deactivate",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "Inactive"
    )


def test_activate_device():

    admin_token = create_admin()

    device = create_device(
        admin_token
    )

    response = client.patch(
        f"/api/v1/devices/{device['id']}/deactivate",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/devices/{device['id']}/activate",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "Active"
    )


def test_block_device():

    admin_token = create_admin()

    device = create_device(
        admin_token
    )

    response = client.patch(
        f"/api/v1/devices/{device['id']}/block",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "Blocked"
    )


def test_mark_device_lost():

    admin_token = create_admin()

    device = create_device(
        admin_token
    )

    response = client.patch(
        f"/api/v1/devices/{device['id']}/lost",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "Lost"
    )


# =========================================================
# LIST / SEARCH / FILTER
# =========================================================

def test_list_devices():

    admin_token = create_admin()

    create_device(
        admin_token
    )

    response = client.get(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_search_device_by_imei():

    admin_token = create_admin()

    device = create_device(
        admin_token
    )

    response = client.get(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        params={
            "search": device["imei"]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["imei"] == device["imei"]
        for item in data
    )


def test_search_device_by_model():

    admin_token = create_admin()

    device = create_device(
        admin_token
    )

    response = client.get(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        params={
            "search": device["model"]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == device["id"]
        for item in data
    )


def test_filter_device_by_type():

    admin_token = create_admin()

    response = client.post(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        json={
            "imei": "356666666666666",
            "model": "Router Filter Test",
            "manufacturer": "TP-Link",
            "device_type": "Router",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        params={
            "device_type": "Router"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        item["device_type"] == "Router"
        for item in data
    )


def test_filter_device_by_status():

    admin_token = create_admin()

    device = create_device(
        admin_token
    )

    block_response = client.patch(
        f"/api/v1/devices/{device['id']}/block",
        headers=auth_headers(admin_token),
    )

    assert block_response.status_code == 200

    response = client.get(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        params={
            "status": "Blocked"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        item["status"] == "Blocked"
        for item in data
    )


def test_filter_device_by_customer():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    device = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    response = client.get(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
        params={
            "customer_id": customer["id"]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == device["id"]
        for item in data
    )


# =========================================================
# SIM ASSIGNMENT
# =========================================================

def test_assign_active_sim_to_device():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    plan = create_plan(
        admin_token
    )

    sim = create_sim(
        admin_token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    device = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    response = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim["id"],
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["device_id"] == device["id"]
    assert data["sim_id"] == sim["id"]
    assert data["is_active"] is True


def test_assign_nonexistent_sim():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    device = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    response = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": 999999,
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "SIM not found"
    )


def test_assign_available_sim_is_rejected():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    sim = create_sim(
        admin_token
    )

    device = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    response = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim["id"],
        },
    )

    assert response.status_code == 400

    assert (
        "active SIM"
        in response.json()["detail"]
    )


def test_assign_sim_without_customer_is_rejected():

    admin_token = create_admin()

    plan = create_plan(
        admin_token
    )

    sim = create_sim(
        admin_token,
        plan_id=plan["id"],
    )

    device = create_device(
        admin_token
    )

    response = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim["id"],
        },
    )

    assert response.status_code == 400


def test_sim_and_device_customer_must_match():

    admin_token = create_admin()

    customer_one = create_customer(
        admin_token
    )

    customer_two = create_customer(
        admin_token
    )

    plan = create_plan(
        admin_token
    )

    sim = create_sim(
        admin_token,
        customer_id=customer_one["id"],
        plan_id=plan["id"],
    )

    device = create_device(
        admin_token,
        customer_id=customer_two["id"],
    )

    response = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim["id"],
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "SIM and device must belong to the same customer"
    )


def test_device_without_customer_cannot_receive_sim():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    plan = create_plan(
        admin_token
    )

    sim = create_sim(
        admin_token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    device = create_device(
        admin_token
    )

    response = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim["id"],
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Device must be assigned to a customer first"
    )


def test_sim_cannot_be_assigned_to_two_devices():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    plan = create_plan(
        admin_token
    )

    sim = create_sim(
        admin_token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    device_one = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    device_two = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    first = client.post(
        f"/api/v1/devices/{device_one['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim["id"],
        },
    )

    assert first.status_code == 201

    second = client.post(
        f"/api/v1/devices/{device_two['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim["id"],
        },
    )

    assert second.status_code == 409

    assert (
        second.json()["detail"]
        == "SIM is already assigned to another active device"
    )


def test_device_cannot_have_two_active_sims():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    plan = create_plan(
        admin_token
    )

    sim_one = create_sim(
        admin_token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    sim_two = create_sim(
        admin_token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    device = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    first = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim_one["id"],
        },
    )

    assert first.status_code == 201

    second = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim_two["id"],
        },
    )

    assert second.status_code == 409

    assert (
        second.json()["detail"]
        == "Device already has an active SIM"
    )


# =========================================================
# CURRENT SIM
# =========================================================

def test_get_current_sim():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    plan = create_plan(
        admin_token
    )

    sim = create_sim(
        admin_token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    device = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    assignment = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim["id"],
        },
    )

    assert assignment.status_code == 201

    response = client.get(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["device_id"] == device["id"]
    assert data["sim_id"] == sim["id"]
    assert data["is_active"] is True


def test_get_current_sim_when_none_assigned():

    admin_token = create_admin()

    device = create_device(
        admin_token
    )

    response = client.get(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404


# =========================================================
# UNASSIGN SIM
# =========================================================

def test_unassign_sim():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    plan = create_plan(
        admin_token
    )

    sim = create_sim(
        admin_token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    device = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    assignment = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim["id"],
        },
    )

    assert assignment.status_code == 201

    response = client.delete(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_active"] is False
    assert data["unassigned_at"] is not None


def test_unassign_without_active_sim():

    admin_token = create_admin()

    device = create_device(
        admin_token
    )

    response = client.delete(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404


# =========================================================
# SIM HISTORY
# =========================================================

def test_sim_assignment_history():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    plan = create_plan(
        admin_token
    )

    sim = create_sim(
        admin_token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    device = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    assignment = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim["id"],
        },
    )

    assert assignment.status_code == 201

    unassignment = client.delete(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
    )

    assert unassignment.status_code == 200

    response = client.get(
        f"/api/v1/devices/{device['id']}/sim-history",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1
    assert data[0]["device_id"] == device["id"]


# =========================================================
# DEACTIVATE DEVICE + SIM
# =========================================================

def test_deactivate_device_deactivates_sim_mapping():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    plan = create_plan(
        admin_token
    )

    sim = create_sim(
        admin_token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    device = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    assignment = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
        json={
            "sim_id": sim["id"],
        },
    )

    assert assignment.status_code == 201

    response = client.patch(
        f"/api/v1/devices/{device['id']}/deactivate",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "Inactive"
    )

    current_sim = client.get(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(admin_token),
    )

    assert current_sim.status_code == 404


# =========================================================
# ROLE TESTS
# =========================================================

def test_customer_cannot_create_device():

    customer_email = unique_email(
        "customer"
    )

    register_user(
        role="CUSTOMER",
        email=customer_email,
    )

    customer_token = login_user(
        customer_email
    )

    response = client.post(
        "/api/v1/devices",
        headers=auth_headers(customer_token),
        json={
            "imei": "357777777777777",
            "model": "Customer Device",
            "manufacturer": "Samsung",
            "device_type": "Smartphone",
        },
    )

    assert response.status_code == 403


def test_customer_can_view_devices():

    admin_token = create_admin()

    create_device(
        admin_token
    )

    customer_email = unique_email(
        "viewer"
    )

    register_user(
        role="CUSTOMER",
        email=customer_email,
    )

    customer_token = login_user(
        customer_email
    )

    response = client.get(
        "/api/v1/devices",
        headers=auth_headers(customer_token),
    )

    assert response.status_code == 200


def test_customer_cannot_assign_sim():

    admin_token = create_admin()

    customer = create_customer(
        admin_token
    )

    plan = create_plan(
        admin_token
    )

    sim = create_sim(
        admin_token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    device = create_device(
        admin_token,
        customer_id=customer["id"],
    )

    customer_email = unique_email(
        "normalcustomer"
    )

    register_user(
        role="CUSTOMER",
        email=customer_email,
    )

    customer_token = login_user(
        customer_email
    )

    response = client.post(
        f"/api/v1/devices/{device['id']}/sim",
        headers=auth_headers(customer_token),
        json={
            "sim_id": sim["id"],
        },
    )

    assert response.status_code == 403