import os
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "telecom_service_network_test"
)

from fastapi.testclient import TestClient

from db.database import Base, engine
from main import app

from tests.integration.test_support_tickets import (
    auth_headers,
    create_customer,
    create_customer_record,
    create_operations_manager,
    create_support_agent,
    login_user,
    register_user,
)


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


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

    token = login_user(
        customer["email"],
        customer["password"],
    )

    return {
        "user": customer,
        "record": customer_record,
        "token": token,
    }


def create_service_request(
    customer_id,
    token,
    request_type="SIM_REPLACEMENT",
    reason="Test service request",
    description="Test service request description",
):
    response = client.post(
        "/api/v1/service-requests",
        json={
            "customer_id": customer_id,
            "request_type": request_type,
            "reason": reason,
            "description": description,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201, response.text

    return response.json()


def update_request_status(
    request_id,
    token,
    new_status,
    remarks=None,
):
    response = client.patch(
        f"/api/v1/service-requests/{request_id}/status",
        json={
            "status": new_status,
            "remarks": remarks,
        },
        headers=auth_headers(token),
    )

    return response


# ============================================================
# CREATE REQUEST TESTS
# ============================================================


def test_create_sim_replacement_request():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
        request_type="SIM_REPLACEMENT",
    )

    assert request["id"] is not None
    assert request["request_number"]
    assert request["customer_id"] == customer["record"]["id"]
    assert request["request_type"] == "SIM_REPLACEMENT"
    assert request["status"] == "PENDING"


def test_create_number_change_request():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
        request_type="NUMBER_CHANGE",
    )

    assert request["request_type"] == "NUMBER_CHANGE"
    assert request["status"] == "PENDING"


def test_create_plan_change_request():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
        request_type="PLAN_CHANGE",
    )

    assert request["request_type"] == "PLAN_CHANGE"
    assert request["status"] == "PENDING"


def test_create_device_replacement_request():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
        request_type="DEVICE_REPLACEMENT",
    )

    assert request["request_type"] == "DEVICE_REPLACEMENT"
    assert request["status"] == "PENDING"


def test_create_service_activation_request():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
        request_type="SERVICE_ACTIVATION",
    )

    assert request["request_type"] == "SERVICE_ACTIVATION"
    assert request["status"] == "PENDING"


def test_create_service_suspension_request():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
        request_type="SERVICE_SUSPENSION",
    )

    assert request["request_type"] == "SERVICE_SUSPENSION"
    assert request["status"] == "PENDING"


def test_create_service_termination_request():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
        request_type="SERVICE_TERMINATION",
    )

    assert request["request_type"] == "SERVICE_TERMINATION"
    assert request["status"] == "PENDING"


# ============================================================
# HISTORY TESTS
# ============================================================


def test_request_creation_creates_initial_history():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
    )

    response = client.get(
        f"/api/v1/service-requests/{request['id']}/history",
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert response.status_code == 200

    history = response.json()

    assert len(history) == 1

    first_history = history[0]

    assert first_history["service_request_id"] == request["id"]
    assert first_history["old_status"] is None
    assert first_history["new_status"] == "PENDING"
    assert first_history["remarks"] == "Service request created"
    assert first_history["changed_by"] is not None
    assert first_history["changed_at"] is not None


# ============================================================
# GET REQUEST TESTS
# ============================================================


def test_get_service_request():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
    )

    response = client.get(
        f"/api/v1/service-requests/{request['id']}",
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == request["id"]
    assert data["request_number"] == request["request_number"]
    assert data["customer_id"] == customer["record"]["id"]
    assert data["request_type"] == "SIM_REPLACEMENT"
    assert data["status"] == "PENDING"


def test_get_service_requests():
    customer = create_customer_with_record()

    create_service_request(
        customer["record"]["id"],
        customer["token"],
    )

    response = client.get(
        "/api/v1/service-requests",
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    for request in data:
        assert request["customer_id"] == customer["record"]["id"]


def test_filter_service_requests_by_customer():
    customer = create_customer_with_record()

    create_service_request(
        customer["record"]["id"],
        customer["token"],
        request_type="SIM_REPLACEMENT",
    )

    create_service_request(
        customer["record"]["id"],
        customer["token"],
        request_type="NUMBER_CHANGE",
    )

    response = client.get(
        "/api/v1/service-requests",
        params={
            "customer_id": customer["record"]["id"]
        },
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 2

    for request in data:
        assert request["customer_id"] == customer["record"]["id"]


def test_filter_service_requests_by_type():
    customer = create_customer_with_record()

    create_service_request(
        customer["record"]["id"],
        customer["token"],
        request_type="SIM_REPLACEMENT",
    )

    create_service_request(
        customer["record"]["id"],
        customer["token"],
        request_type="NUMBER_CHANGE",
    )

    response = client.get(
        "/api/v1/service-requests",
        params={
            "request_type": "SIM_REPLACEMENT"
        },
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for request in data:
        assert request["request_type"] == "SIM_REPLACEMENT"


# ============================================================
# ACCESS CONTROL TESTS
# ============================================================


def test_customer_can_access_own_request():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
    )

    response = client.get(
        f"/api/v1/service-requests/{request['id']}",
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert response.status_code == 200


def test_customer_cannot_access_other_customer_request():
    customer_one = create_customer_with_record()
    customer_two = create_customer_with_record()

    request = create_service_request(
        customer_one["record"]["id"],
        customer_one["token"],
    )

    response = client.get(
        f"/api/v1/service-requests/{request['id']}",
        headers=auth_headers(
            customer_two["token"]
        ),
    )

    assert response.status_code == 403


# ============================================================
# STATUS UPDATE TESTS
# ============================================================


def test_staff_can_update_request_status():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
    )

    operations_manager = create_operations_manager()

    staff_token = login_user(
        operations_manager["email"],
        operations_manager["password"],
    )

    response = update_request_status(
        request["id"],
        staff_token,
        "IN_PROGRESS",
        "Request is being processed",
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == request["id"]
    assert data["status"] == "IN_PROGRESS"


def test_customer_cannot_update_request_status():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
    )

    response = update_request_status(
        request["id"],
        customer["token"],
        "IN_PROGRESS",
        "Customer attempting status update",
    )

    assert response.status_code == 403


def test_complete_service_request_status_flow():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
    )

    operations_manager = create_operations_manager()

    staff_token = login_user(
        operations_manager["email"],
        operations_manager["password"],
    )

    response = update_request_status(
        request["id"],
        staff_token,
        "IN_PROGRESS",
        "Started processing",
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"

    response = update_request_status(
        request["id"],
        staff_token,
        "APPROVED",
        "Request approved",
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"

    response = update_request_status(
        request["id"],
        staff_token,
        "COMPLETED",
        "Request completed",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "COMPLETED"
    assert data["completed_at"] is not None


# ============================================================
# COMPLETE HISTORY TEST
# ============================================================


def test_complete_status_history_is_created():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
    )

    support_agent = create_support_agent()

    staff_token = login_user(
        support_agent["email"],
        support_agent["password"],
    )

    response = update_request_status(
        request["id"],
        staff_token,
        "IN_PROGRESS",
        "Processing started",
    )

    assert response.status_code == 200

    response = update_request_status(
        request["id"],
        staff_token,
        "APPROVED",
        "Approved by support",
    )

    assert response.status_code == 200

    response = update_request_status(
        request["id"],
        staff_token,
        "COMPLETED",
        "Completed successfully",
    )

    assert response.status_code == 200

    response = client.get(
        f"/api/v1/service-requests/{request['id']}/history",
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert response.status_code == 200

    history = response.json()

    assert len(history) == 4

    assert history[0]["old_status"] is None
    assert history[0]["new_status"] == "PENDING"

    assert history[1]["old_status"] == "PENDING"
    assert history[1]["new_status"] == "IN_PROGRESS"

    assert history[2]["old_status"] == "IN_PROGRESS"
    assert history[2]["new_status"] == "APPROVED"

    assert history[3]["old_status"] == "APPROVED"
    assert history[3]["new_status"] == "COMPLETED"


# ============================================================
# INVALID TRANSITION TEST
# ============================================================


def test_invalid_status_transition_is_rejected():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
    )

    operations_manager = create_operations_manager()

    staff_token = login_user(
        operations_manager["email"],
        operations_manager["password"],
    )

    response = update_request_status(
        request["id"],
        staff_token,
        "COMPLETED",
        "Invalid transition",
    )

    assert response.status_code == 400

    assert (
        "Invalid status transition"
        in response.json()["detail"]
    )


# ============================================================
# SAME STATUS TEST
# ============================================================


def test_same_status_update_is_rejected():
    customer = create_customer_with_record()

    request = create_service_request(
        customer["record"]["id"],
        customer["token"],
    )

    operations_manager = create_operations_manager()

    staff_token = login_user(
        operations_manager["email"],
        operations_manager["password"],
    )

    response = update_request_status(
        request["id"],
        staff_token,
        "PENDING",
        "Same status",
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Service request already has this status"
    )


# ============================================================
# 404 TESTS
# ============================================================


def test_get_non_existing_service_request():
    customer = create_customer_with_record()

    response = client.get(
        "/api/v1/service-requests/999999",
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Service request not found"
    )


def test_history_for_non_existing_request():
    customer = create_customer_with_record()

    response = client.get(
        "/api/v1/service-requests/999999/history",
        headers=auth_headers(
            customer["token"]
        ),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Service request not found"
    )