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


def unique_email(prefix="user"):
    safe_prefix = prefix.lower().replace(" ", "_")
    return f"{safe_prefix}_{uuid4().hex[:8]}@example.com"


def register_user(
    role="Customer",
):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Test {role}",
            "email": unique_email(role),
            "phone": "9876543210",
            "password": "Password123",
            "role": role,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def login(email):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Password123",
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def create_customer_profile(
    admin_token,
    customer_id,
):
    response = client.post(
        "/api/v1/customers",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
        json={
            "user_id": customer_id,
            "customer_number": (
                f"CUST-{uuid4().hex[:8]}"
            ),
            "address_line1": "Main Street",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "postal_code": "517501",
            "country": "India",
            "kyc_status": "Pending",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def test_customer_history_created_on_customer_creation():

    admin = register_user("Super Admin")
    customer = register_user("Customer")

    admin_token = login(admin["email"])

    created = create_customer_profile(
        admin_token,
        customer["id"],
    )

    response = client.get(
        f"/api/v1/customers/{created['id']}/history",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert response.status_code == 200, response.text

    history = response.json()

    assert len(history) >= 1

    created_history = [
        item
        for item in history
        if item["action"] == "CUSTOMER_CREATED"
    ]

    assert len(created_history) == 1

    item = created_history[0]

    assert item["customer_id"] == created["id"]
    assert item["changed_by"] == admin["id"]
    assert item["action"] == "CUSTOMER_CREATED"


def test_customer_update_creates_history():

    admin = register_user("Super Admin")
    customer = register_user("Customer")

    admin_token = login(admin["email"])

    created = create_customer_profile(
        admin_token,
        customer["id"],
    )

    response = client.patch(
        f"/api/v1/customers/{created['id']}",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
        json={
            "city": "Hyderabad",
            "state": "Telangana",
        },
    )

    assert response.status_code == 200, response.text

    history_response = client.get(
        f"/api/v1/customers/{created['id']}/history",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert history_response.status_code == 200

    history = history_response.json()

    update_history = [
        item
        for item in history
        if item["action"] == "CUSTOMER_UPDATED"
    ]

    assert len(update_history) >= 1

    latest = update_history[0]

    assert latest["changed_by"] == admin["id"]
    assert latest["previous_value"]["city"] == "Tirupati"
    assert latest["new_value"]["city"] == "Hyderabad"


def test_customer_deactivation_creates_history():

    admin = register_user("Super Admin")
    customer = register_user("Customer")

    admin_token = login(admin["email"])

    created = create_customer_profile(
        admin_token,
        customer["id"],
    )

    response = client.patch(
        f"/api/v1/customers/{created['id']}/deactivate",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["is_active"] is False

    history_response = client.get(
        f"/api/v1/customers/{created['id']}/history",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert history_response.status_code == 200

    history = history_response.json()

    deactivation_history = [
        item
        for item in history
        if item["action"] == "CUSTOMER_DEACTIVATED"
    ]

    assert len(deactivation_history) >= 1

    latest = deactivation_history[0]

    assert latest["changed_by"] == admin["id"]
    assert (
        latest["new_value"]["customer_is_active"]
        is False
    )


def test_customer_activation_creates_history():

    admin = register_user("Super Admin")
    customer = register_user("Customer")

    admin_token = login(admin["email"])

    created = create_customer_profile(
        admin_token,
        customer["id"],
    )

    deactivate_response = client.patch(
        f"/api/v1/customers/{created['id']}/deactivate",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert deactivate_response.status_code == 200

    response = client.patch(
        f"/api/v1/customers/{created['id']}/activate",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["is_active"] is True

    history_response = client.get(
        f"/api/v1/customers/{created['id']}/history",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert history_response.status_code == 200

    history = history_response.json()

    activation_history = [
        item
        for item in history
        if item["action"] == "CUSTOMER_ACTIVATED"
    ]

    assert len(activation_history) >= 1

    latest = activation_history[0]

    assert latest["changed_by"] == admin["id"]
    assert (
        latest["new_value"]["customer_is_active"]
        is True
    )


def test_nonexistent_customer_history_returns_404():

    admin = register_user("Super Admin")

    admin_token = login(admin["email"])

    response = client.get(
        "/api/v1/customers/999999/history",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert response.status_code == 404