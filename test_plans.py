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
    safe_prefix = prefix.lower().replace(
        " ",
        "_",
    )

    return (
        f"{safe_prefix}_{uuid4().hex[:8]}"
        "@example.com"
    )


def register_user(role="Customer"):
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


def create_plan(
    token,
    plan_name=None,
    plan_type="Prepaid",
    validity_days=28,
    data_limit_mb=10000,
    voice_limit_minutes=500,
    sms_limit=100,
    price=299.0,
):
    if plan_name is None:
        plan_name = (
            f"Plan-{uuid4().hex[:8]}"
        )

    response = client.post(
        "/api/v1/plans",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "plan_name": plan_name,
            "description": "Test telecom plan",
            "plan_type": plan_type,
            "validity_days": validity_days,
            "data_limit_mb": data_limit_mb,
            "voice_limit_minutes": (
                voice_limit_minutes
            ),
            "sms_limit": sms_limit,
            "price": price,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def test_create_prepaid_plan():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan = create_plan(
        token,
        plan_type="Prepaid",
    )

    assert plan["plan_type"] == "Prepaid"
    assert plan["validity_days"] == 28
    assert plan["data_limit_mb"] == 10000
    assert plan["voice_limit_minutes"] == 500
    assert plan["sms_limit"] == 100
    assert plan["status"] == "Active"


def test_create_postpaid_plan():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan = create_plan(
        token,
        plan_type="Postpaid",
    )

    assert plan["plan_type"] == "Postpaid"


def test_create_data_plan():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan = create_plan(
        token,
        plan_type="Data",
        voice_limit_minutes=0,
        sms_limit=0,
    )

    assert plan["plan_type"] == "Data"
    assert plan["data_limit_mb"] > 0


def test_create_voice_plan():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan = create_plan(
        token,
        plan_type="Voice",
        data_limit_mb=0,
        sms_limit=0,
    )

    assert plan["plan_type"] == "Voice"
    assert plan["voice_limit_minutes"] > 0


def test_create_sms_plan():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan = create_plan(
        token,
        plan_type="SMS",
        data_limit_mb=0,
        voice_limit_minutes=0,
    )

    assert plan["plan_type"] == "SMS"
    assert plan["sms_limit"] > 0


def test_update_plan():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan = create_plan(token)

    response = client.patch(
        f"/api/v1/plans/{plan['id']}",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "validity_days": 56,
            "data_limit_mb": 20000,
            "price": 499.0,
        },
    )

    assert response.status_code == 200, response.text

    updated = response.json()

    assert updated["validity_days"] == 56
    assert updated["data_limit_mb"] == 20000
    assert updated["price"] == 499.0


def test_deactivate_plan():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan = create_plan(token)

    response = client.patch(
        f"/api/v1/plans/{plan['id']}/deactivate",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Inactive"


def test_activate_plan():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan = create_plan(token)

    client.patch(
        f"/api/v1/plans/{plan['id']}/deactivate",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    response = client.patch(
        f"/api/v1/plans/{plan['id']}/activate",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Active"


def test_search_plans():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan_name = (
        f"UnlimitedData-{uuid4().hex[:8]}"
    )

    create_plan(
        token,
        plan_name=plan_name,
        plan_type="Data",
    )

    response = client.get(
        "/api/v1/plans",
        params={
            "search": "UnlimitedData"
        },
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    plans = response.json()

    assert len(plans) >= 1
    assert any(
        "UnlimitedData" in plan["plan_name"]
        for plan in plans
    )


def test_filter_plans_by_type():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    create_plan(
        token,
        plan_type="Data",
    )

    response = client.get(
        "/api/v1/plans",
        params={
            "plan_type": "Data"
        },
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    plans = response.json()

    assert len(plans) >= 1

    assert all(
        plan["plan_type"] == "Data"
        for plan in plans
    )


def test_filter_plans_by_status():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan = create_plan(token)

    client.patch(
        f"/api/v1/plans/{plan['id']}/deactivate",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    response = client.get(
        "/api/v1/plans",
        params={
            "status": "Inactive"
        },
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    plans = response.json()

    assert len(plans) >= 1

    assert all(
        plan["status"] == "Inactive"
        for plan in plans
    )


def test_duplicate_plan_name_not_allowed():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan_name = (
        f"Duplicate-{uuid4().hex[:8]}"
    )

    create_plan(
        token,
        plan_name=plan_name,
    )

    response = client.post(
        "/api/v1/plans",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "plan_name": plan_name,
            "description": "Duplicate",
            "plan_type": "Prepaid",
            "validity_days": 28,
            "data_limit_mb": 1000,
            "voice_limit_minutes": 100,
            "sms_limit": 100,
            "price": 199.0,
        },
    )

    assert response.status_code == 409


def test_plan_comparison():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan_one = create_plan(
        token,
        plan_type="Prepaid",
        data_limit_mb=10000,
        voice_limit_minutes=500,
        sms_limit=100,
        price=299,
    )

    plan_two = create_plan(
        token,
        plan_type="Postpaid",
        data_limit_mb=20000,
        voice_limit_minutes=1000,
        sms_limit=200,
        price=599,
    )

    response = client.get(
        "/api/v1/plans/compare",
        params=[
            ("plan_ids", plan_one["id"]),
            ("plan_ids", plan_two["id"]),
        ],
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    comparison = response.json()

    assert len(comparison) == 2

    assert comparison[0]["id"] == plan_one["id"]
    assert comparison[1]["id"] == plan_two["id"]

    assert (
        comparison[0]["data_limit_mb"]
        != comparison[1]["data_limit_mb"]
    )


def test_customer_can_view_plans():

    admin = register_user("Super Admin")
    customer = register_user("Customer")

    admin_token = login(admin["email"])
    customer_token = login(customer["email"])

    create_plan(admin_token)

    response = client.get(
        "/api/v1/plans",
        headers={
            "Authorization": (
                f"Bearer {customer_token}"
            )
        },
    )

    assert response.status_code == 200


def test_customer_cannot_create_plan():

    customer = register_user("Customer")
    token = login(customer["email"])

    response = client.post(
        "/api/v1/plans",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "plan_name": (
                f"CustomerPlan-{uuid4().hex[:8]}"
            ),
            "description": "Not allowed",
            "plan_type": "Prepaid",
            "validity_days": 28,
            "data_limit_mb": 1000,
            "voice_limit_minutes": 100,
            "sms_limit": 100,
            "price": 199.0,
        },
    )

    assert response.status_code == 403