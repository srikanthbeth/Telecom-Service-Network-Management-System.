import os
import uuid

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


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def unique_email():
    return f"customer_{uuid.uuid4().hex}@example.com"


def register_customer():
    email = unique_email()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Customer One",
            "email": email,
            "phone": "9876543210",
            "password": "Password@123",
            "role": "Customer",
        },
    )

    assert response.status_code == 201

    return response.json()


def register_admin():
    email = unique_email()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Super Admin",
            "email": email,
            "phone": "9876543211",
            "password": "Password@123",
            "role": "Super Admin",
        },
    )

    assert response.status_code == 201

    return response.json()


def login(email):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Password@123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_customer_profile(
    admin_token,
    user_id,
    customer_number=None,
):
    if customer_number is None:
        customer_number = (
            f"CUST-{uuid.uuid4().hex[:10]}"
        )

    return client.post(
        "/api/v1/customers",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
        json={
            "user_id": user_id,
            "customer_number": customer_number,
            "address_line1": "Main Road",
            "address_line2": "Near Bus Stand",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "postal_code": "517501",
            "country": "India",
            "kyc_status": "Pending",
        },
    )


def test_create_customer_profile():
    admin = register_admin()
    customer = register_customer()

    admin_token = login(
        admin["email"]
    )

    response = create_customer_profile(
        admin_token,
        customer["id"],
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == customer["id"]
    assert data["customer_number"].startswith(
        "CUST-"
    )
    assert data["city"] == "Tirupati"
    assert data["state"] == "Andhra Pradesh"
    assert data["kyc_status"] == "Pending"
    assert data["is_active"] is True


def test_get_customer():
    admin = register_admin()
    customer = register_customer()

    admin_token = login(
        admin["email"]
    )

    created = create_customer_profile(
        admin_token,
        customer["id"],
    )

    customer_id = created.json()["id"]

    response = client.get(
        f"/api/v1/customers/{customer_id}",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == customer_id


def test_update_customer():
    admin = register_admin()
    customer = register_customer()

    admin_token = login(
        admin["email"]
    )

    created = create_customer_profile(
        admin_token,
        customer["id"],
    )

    customer_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/customers/{customer_id}",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
        json={
            "city": "Chittoor",
            "postal_code": "517001",
            "kyc_status": "Verified",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["city"] == "Chittoor"
    assert data["postal_code"] == "517001"
    assert data["kyc_status"] == "Verified"


def test_duplicate_customer_profile_not_allowed():
    admin = register_admin()
    customer = register_customer()

    admin_token = login(
        admin["email"]
    )

    first = create_customer_profile(
        admin_token,
        customer["id"],
    )

    assert first.status_code == 201

    second = create_customer_profile(
        admin_token,
        customer["id"],
    )

    assert second.status_code == 409


def test_duplicate_customer_number_not_allowed():
    admin = register_admin()

    customer_one = register_customer()
    customer_two = register_customer()

    admin_token = login(
        admin["email"]
    )

    customer_number = (
        f"CUST-{uuid.uuid4().hex[:10]}"
    )

    first = create_customer_profile(
        admin_token,
        customer_one["id"],
        customer_number,
    )

    assert first.status_code == 201

    second = create_customer_profile(
        admin_token,
        customer_two["id"],
        customer_number,
    )

    assert second.status_code == 409


def test_customer_search():
    admin = register_admin()
    customer = register_customer()

    admin_token = login(
        admin["email"]
    )

    create_customer_profile(
        admin_token,
        customer["id"],
    )

    response = client.get(
        "/api/v1/customers",
        params={
            "search": "Customer One"
        },
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    assert any(
        item["user_id"] == customer["id"]
        for item in data
    )


def test_filter_by_kyc_status():
    admin = register_admin()
    customer = register_customer()

    admin_token = login(
        admin["email"]
    )

    create_customer_profile(
        admin_token,
        customer["id"],
    )

    response = client.get(
        "/api/v1/customers",
        params={
            "kyc_status": "Pending"
        },
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    assert all(
        item["kyc_status"] == "Pending"
        for item in data
    )


def test_filter_by_active_status():
    admin = register_admin()
    customer = register_customer()

    admin_token = login(
        admin["email"]
    )

    create_customer_profile(
        admin_token,
        customer["id"],
    )

    response = client.get(
        "/api/v1/customers",
        params={
            "is_active": True
        },
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    assert all(
        item["is_active"] is True
        for item in data
    )


def test_deactivate_customer():
    admin = register_admin()
    customer = register_customer()

    admin_token = login(
        admin["email"]
    )

    created = create_customer_profile(
        admin_token,
        customer["id"],
    )

    customer_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/customers/{customer_id}/deactivate",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_activate_customer():
    admin = register_admin()
    customer = register_customer()

    admin_token = login(
        admin["email"]
    )

    created = create_customer_profile(
        admin_token,
        customer["id"],
    )

    customer_id = created.json()["id"]

    deactivate = client.patch(
        f"/api/v1/customers/{customer_id}/deactivate",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert deactivate.status_code == 200

    activate = client.patch(
        f"/api/v1/customers/{customer_id}/activate",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert activate.status_code == 200
    assert activate.json()["is_active"] is True


def test_customer_cannot_create_customer_profile():
    customer = register_customer()

    customer_token = login(
        customer["email"]
    )

    another_customer = register_customer()

    response = create_customer_profile(
        customer_token,
        another_customer["id"],
    )

    assert response.status_code == 403


def test_customer_cannot_update_customer_profile():
    admin = register_admin()
    customer = register_customer()

    admin_token = login(
        admin["email"]
    )

    created = create_customer_profile(
        admin_token,
        customer["id"],
    )

    customer_id = created.json()["id"]

    customer_token = login(
        customer["email"]
    )

    response = client.patch(
        f"/api/v1/customers/{customer_id}",
        headers={
            "Authorization": (
                f"Bearer {customer_token}"
            )
        },
        json={
            "city": "Hyderabad"
        },
    )

    assert response.status_code == 403


def test_nonexistent_customer_returns_404():
    admin = register_admin()

    admin_token = login(
        admin["email"]
    )

    response = client.get(
        "/api/v1/customers/999999",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Customer not found"
    )