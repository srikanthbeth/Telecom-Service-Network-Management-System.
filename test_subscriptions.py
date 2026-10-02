import os
from datetime import date, timedelta
from uuid import uuid4


# =========================================================
# TEST DATABASE
# =========================================================

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "telecom_service_network_test"
)


from fastapi.testclient import TestClient
from sqlalchemy import text

from db.database import Base, SessionLocal, engine
from main import app


client = TestClient(app)


# =========================================================
# SETUP
# =========================================================

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# =========================================================
# HELPERS
# =========================================================

def unique_email(prefix="subscription"):
    return f"{prefix}_{uuid4().hex}@example.com"


def register_user(
    role="Customer",
    email=None,
):
    if email is None:
        email = unique_email()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Test {role}",
            "email": email,
            "phone": f"9{uuid4().int % 10**9:09d}",
            "password": "Test@123456",
            "role": role,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def login_user(
    email,
    password="Test@123456",
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


def create_customer(
    admin_token,
):
    user = register_user(
        role="Customer"
    )

    response = client.post(
        "/api/v1/customers",
        headers=auth_headers(admin_token),
        json={
            "user_id": user["id"],
            "customer_number": (
                f"CUST-SUB-{uuid4().hex[:10].upper()}"
            ),
            "kyc_status": "Verified",
            "address": "Test Address",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_plan(
    admin_token,
    name=None,
):
    # Always make the plan name unique.
    # This prevents 409 conflicts between test functions.
    if name is None:
        name = f"SUB-PLAN-{uuid4().hex[:8].upper()}"
    else:
        name = f"{name}-{uuid4().hex[:8].upper()}"

    response = client.post(
        "/api/v1/plans",
        headers=auth_headers(admin_token),
        json={
            "plan_name": name,
            "description": "Subscription test plan",
            "plan_type": "Data",
            "price": 499.0,
            "validity_days": 30,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_sim(
    admin_token,
    customer_id,
    plan_id,
):
    response = client.post(
        "/api/v1/sims",
        headers=auth_headers(admin_token),
        json={
            "sim_number": (
                f"SIM-SUB-{uuid4().hex[:10].upper()}"
            ),
            "sim_type": "Physical",
            "customer_id": customer_id,
            "plan_id": plan_id,
        },
    )

    assert response.status_code == 201, response.text

    sim = response.json()

    response = client.patch(
        f"/api/v1/sims/{sim['id']}/activate",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200, response.text

    return sim


def create_subscription(
    admin_token,
    customer_id,
    sim_id,
    plan_id,
):
    start_date = date.today()
    end_date = start_date + timedelta(days=30)

    response = client.post(
        "/api/v1/subscriptions",
        headers=auth_headers(admin_token),
        json={
            "customer_id": customer_id,
            "sim_id": sim_id,
            "plan_id": plan_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_complete_setup():
    # -----------------------------------------------------
    # Create admin
    # -----------------------------------------------------

    admin = register_user(
        role="Super Admin"
    )

    admin_token = login_user(
        admin["email"]
    )

    # -----------------------------------------------------
    # Create customer
    # -----------------------------------------------------

    customer = create_customer(
        admin_token
    )

    # -----------------------------------------------------
    # Create three unique plans
    # -----------------------------------------------------

    plan1 = create_plan(
        admin_token,
        "Basic Subscription",
    )

    plan2 = create_plan(
        admin_token,
        "Premium Subscription",
    )

    plan3 = create_plan(
        admin_token,
        "Enterprise Subscription",
    )

    # -----------------------------------------------------
    # Create SIM
    # -----------------------------------------------------

    sim = create_sim(
        admin_token,
        customer["id"],
        plan1["id"],
    )

    # -----------------------------------------------------
    # Create subscription
    # -----------------------------------------------------

    subscription = create_subscription(
        admin_token,
        customer["id"],
        sim["id"],
        plan1["id"],
    )

    return {
        "token": admin_token,
        "customer": customer,
        "plan1": plan1,
        "plan2": plan2,
        "plan3": plan3,
        "sim": sim,
        "subscription": subscription,
    }


# =========================================================
# CREATE SUBSCRIPTION
# =========================================================

def test_create_subscription():

    data = create_complete_setup()

    subscription = data["subscription"]

    assert subscription["customer_id"] == (
        data["customer"]["id"]
    )

    assert subscription["sim_id"] == (
        data["sim"]["id"]
    )

    assert subscription["plan_id"] == (
        data["plan1"]["id"]
    )

    assert subscription["status"] == "Active"


def test_subscription_dates_are_returned():

    data = create_complete_setup()

    subscription = data["subscription"]

    assert subscription["start_date"]
    assert subscription["end_date"]


def test_duplicate_active_subscription_for_sim_fails():

    data = create_complete_setup()

    start_date = date.today()
    end_date = start_date + timedelta(days=30)

    response = client.post(
        "/api/v1/subscriptions",
        headers=auth_headers(data["token"]),
        json={
            "customer_id": data["customer"]["id"],
            "sim_id": data["sim"]["id"],
            "plan_id": data["plan2"]["id"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "SIM already has an active subscription"
    )


def test_invalid_date_range_fails():

    data = create_complete_setup()

    start_date = date.today()
    end_date = start_date

    response = client.post(
        "/api/v1/subscriptions",
        headers=auth_headers(data["token"]),
        json={
            "customer_id": data["customer"]["id"],
            "sim_id": data["sim"]["id"],
            "plan_id": data["plan2"]["id"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "End date must be after start date"
    )


# =========================================================
# GET
# =========================================================

def test_get_subscription():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.get(
        f"/api/v1/subscriptions/{subscription_id}",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == subscription_id


def test_get_nonexistent_subscription():

    data = create_complete_setup()

    response = client.get(
        "/api/v1/subscriptions/999999",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 404


# =========================================================
# LIST
# =========================================================

def test_list_subscriptions():

    data = create_complete_setup()

    response = client.get(
        "/api/v1/subscriptions",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    subscriptions = response.json()

    assert isinstance(subscriptions, list)
    assert len(subscriptions) >= 1


def test_filter_subscriptions_by_customer():

    data = create_complete_setup()

    response = client.get(
        "/api/v1/subscriptions",
        params={
            "customer_id": data["customer"]["id"]
        },
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    for subscription in response.json():
        assert subscription["customer_id"] == (
            data["customer"]["id"]
        )


# =========================================================
# PLAN UPGRADE
# =========================================================

def test_plan_upgrade():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/upgrade",
        headers=auth_headers(data["token"]),
        json={
            "plan_id": data["plan2"]["id"]
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["plan_id"] == data["plan2"]["id"]
    assert body["status"] == "Active"


def test_upgrade_creates_history():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/upgrade",
        headers=auth_headers(data["token"]),
        json={
            "plan_id": data["plan2"]["id"]
        },
    )

    assert response.status_code == 200

    response = client.get(
        f"/api/v1/subscriptions/{subscription_id}/history",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    history = response.json()

    assert any(
        item["action"] == "Plan Upgrade"
        for item in history
    )


# =========================================================
# PLAN DOWNGRADE
# =========================================================

def test_plan_downgrade():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    # First change to another plan
    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/upgrade",
        headers=auth_headers(data["token"]),
        json={
            "plan_id": data["plan2"]["id"]
        },
    )

    assert response.status_code == 200

    # Then downgrade
    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/downgrade",
        headers=auth_headers(data["token"]),
        json={
            "plan_id": data["plan1"]["id"]
        },
    )

    assert response.status_code == 200

    assert response.json()["plan_id"] == (
        data["plan1"]["id"]
    )


def test_same_plan_change_fails():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/upgrade",
        headers=auth_headers(data["token"]),
        json={
            "plan_id": data["plan1"]["id"]
        },
    )

    assert response.status_code == 400


# =========================================================
# RENEWAL
# =========================================================

def test_subscription_renewal():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    new_end_date = (
        date.today() + timedelta(days=90)
    )

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/renew",
        headers=auth_headers(data["token"]),
        json={
            "end_date": new_end_date.isoformat()
        },
    )

    assert response.status_code == 200

    assert response.json()["end_date"] == (
        new_end_date.isoformat()
    )


def test_renewal_with_old_date_fails():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    old_date = date.today() + timedelta(days=10)

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/renew",
        headers=auth_headers(data["token"]),
        json={
            "end_date": old_date.isoformat()
        },
    )

    assert response.status_code == 400


# =========================================================
# SUSPENSION
# =========================================================

def test_subscription_suspension():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/suspend",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    assert response.json()["status"] == "Suspended"


def test_suspend_twice_fails():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/suspend",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/suspend",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 400


# =========================================================
# REACTIVATION
# =========================================================

def test_subscription_reactivation():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/suspend",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/reactivate",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    assert response.json()["status"] == "Active"


def test_reactivate_active_subscription_fails():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/reactivate",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 400


# =========================================================
# CANCELLATION
# =========================================================

def test_subscription_cancellation():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/cancel",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    assert response.json()["status"] == "Cancelled"


def test_cancel_twice_fails():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/cancel",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/cancel",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 400


def test_cancelled_subscription_cannot_be_renewed():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/cancel",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    new_end_date = (
        date.today() + timedelta(days=90)
    )

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/renew",
        headers=auth_headers(data["token"]),
        json={
            "end_date": new_end_date.isoformat()
        },
    )

    assert response.status_code == 400


# =========================================================
# HISTORY
# =========================================================

def test_subscription_history():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.get(
        f"/api/v1/subscriptions/{subscription_id}/history",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    history = response.json()

    assert isinstance(history, list)
    assert len(history) >= 1


def test_history_contains_creation():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.get(
        f"/api/v1/subscriptions/{subscription_id}/history",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    history = response.json()

    assert any(
        item["action"] == "Created"
        for item in history
    )


def test_history_after_suspend_and_reactivate():

    data = create_complete_setup()

    subscription_id = data["subscription"]["id"]

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/suspend",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/subscriptions/{subscription_id}/reactivate",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    response = client.get(
        f"/api/v1/subscriptions/{subscription_id}/history",
        headers=auth_headers(data["token"]),
    )

    assert response.status_code == 200

    actions = [
        item["action"]
        for item in response.json()
    ]

    assert "Created" in actions
    assert "Suspended" in actions
    assert "Reactivated" in actions