import os
from datetime import date, timedelta
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


# ============================================================
# HELPERS
# ============================================================

def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def unique_email(prefix="user"):
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def unique_phone():
    return f"9{uuid4().int % 1000000000:09d}"


def login_user(email, password="Test@123456"):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def register_user(
    role="Customer",
    email=None,
    full_name=None,
):
    email = email or unique_email(role.lower().replace(" ", "_"))
    full_name = full_name or f"Test {role}"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "phone": unique_phone(),
            "password": "Test@123456",
            "role": role,
        },
    )

    assert response.status_code in (200, 201), response.text

    return response.json()


def create_admin():
    email = unique_email("admin")

    register_user(
        role="Super Admin",
        email=email,
        full_name="Usage Test Admin",
    )

    return login_user(email)


def create_customer(admin_token):
    email = unique_email("customer")

    # First create the Customer login/user
    user = register_user(
        role="Customer",
        email=email,
        full_name="Usage Test Customer",
    )

    response = client.post(
        "/api/v1/customers",
        headers=auth_headers(admin_token),
        json={
            "user_id": user["id"],
            "customer_number": f"CUST-{uuid4().hex[:10].upper()}",
            "full_name": "Usage Test Customer",
            "email": email,
            "phone": unique_phone(),
            "address": "Tirupati",
            "kyc_status": "Verified",
        },
    )

    assert response.status_code in (200, 201), response.text

    return response.json()

def create_plan(admin_token, name=None):
    if name is None:
        name = f"USAGE-PLAN-{uuid4().hex[:8].upper()}"
    else:
        name = f"{name}-{uuid4().hex[:8].upper()}"

    response = client.post(
        "/api/v1/plans",
        headers=auth_headers(admin_token),
        json={
            "plan_name": name,
            "description": "Usage tracking test plan",
            "plan_type": "Data",
            "validity_days": 30,
            "data_limit_mb": 5000,
            "voice_limit_minutes": 1000,
            "sms_limit": 500,
            "price": 499.0,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_sim(admin_token, customer_id, plan_id):
    sim_number = f"SIM-{uuid4().hex[:12].upper()}"

    response = client.post(
        "/api/v1/sims",
        headers=auth_headers(admin_token),
        json={
            "sim_number": sim_number,
            "sim_type": "Physical",
            "customer_id": customer_id,
            "plan_id": plan_id,
        },
    )

    assert response.status_code in (200, 201), response.text

    return response.json()


def activate_sim(admin_token, sim_id):
    response = client.patch(
        f"/api/v1/sims/{sim_id}/activate",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200, response.text

    return response.json()


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
    """
    Creates:

    Admin
      ↓
    Customer
      ↓
    Plan
      ↓
    SIM
      ↓
    Active SIM
      ↓
    Subscription
    """

    admin_token = create_admin()

    customer = create_customer(admin_token)

    plan = create_plan(admin_token)

    sim = create_sim(
        admin_token,
        customer["id"],
        plan["id"],
    )

    activate_sim(
        admin_token,
        sim["id"],
    )

    subscription = create_subscription(
        admin_token,
        customer["id"],
        sim["id"],
        plan["id"],
    )

    return {
        "admin_token": admin_token,
        "customer": customer,
        "plan": plan,
        "sim": sim,
        "subscription": subscription,
    }


def create_usage(
    admin_token,
    customer_id,
    sim_id,
    subscription_id,
    usage_type="Data",
    quantity=100,
    usage_date=None,
):
    usage_date = usage_date or date.today()

    response = client.post(
        "/api/v1/usage",
        headers=auth_headers(admin_token),
        json={
            "customer_id": customer_id,
            "sim_id": sim_id,
            "subscription_id": subscription_id,
            "usage_type": usage_type,
            "usage_date": usage_date.isoformat(),
            "quantity": quantity,
        },
    )

    return response


# ============================================================
# 1. CREATE DATA USAGE
# ============================================================

def test_create_data_usage():
    setup = create_complete_setup()

    response = create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        quantity=500,
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["id"] > 0
    assert data["customer_id"] == setup["customer"]["id"]
    assert data["sim_id"] == setup["sim"]["id"]
    assert data["subscription_id"] == setup["subscription"]["id"]
    assert data["usage_type"] == "Data"
    assert data["quantity"] == 500


# ============================================================
# 2. CREATE VOICE USAGE
# ============================================================

def test_create_voice_usage():
    setup = create_complete_setup()

    response = create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Voice",
        quantity=45,
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["usage_type"] == "Voice"
    assert data["quantity"] == 45


# ============================================================
# 3. CREATE SMS USAGE
# ============================================================

def test_create_sms_usage():
    setup = create_complete_setup()

    response = create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="SMS",
        quantity=25,
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["usage_type"] == "SMS"
    assert data["quantity"] == 25


# ============================================================
# 4. GET USAGE
# ============================================================

def test_get_usage():
    setup = create_complete_setup()

    create_response = create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        quantity=250,
    )

    assert create_response.status_code == 201, create_response.text

    usage_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/usage/{usage_id}",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == usage_id
    assert data["quantity"] == 250


# ============================================================
# 5. GET NONEXISTENT USAGE
# ============================================================

def test_get_nonexistent_usage():
    setup = create_complete_setup()

    response = client.get(
        "/api/v1/usage/999999999",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 404


# ============================================================
# 6. LIST USAGE
# ============================================================

def test_list_usage():
    setup = create_complete_setup()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        quantity=100,
    )

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Voice",
        quantity=20,
    )

    response = client.get(
        "/api/v1/usage",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 2


# ============================================================
# 7. FILTER BY CUSTOMER
# ============================================================

def test_list_usage_by_customer():
    setup = create_complete_setup()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        quantity=300,
    )

    response = client.get(
        f"/api/v1/usage?customer_id={setup['customer']['id']}",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) >= 1

    for item in data:
        assert item["customer_id"] == setup["customer"]["id"]


# ============================================================
# 8. FILTER BY SIM
# ============================================================

def test_list_usage_by_sim():
    setup = create_complete_setup()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        quantity=350,
    )

    response = client.get(
        f"/api/v1/usage?sim_id={setup['sim']['id']}",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) >= 1

    for item in data:
        assert item["sim_id"] == setup["sim"]["id"]


# ============================================================
# 9. FILTER BY USAGE TYPE
# ============================================================

def test_list_usage_by_type():
    setup = create_complete_setup()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        quantity=400,
    )

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Voice",
        quantity=30,
    )

    response = client.get(
        "/api/v1/usage?usage_type=Data",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) >= 1

    for item in data:
        assert item["usage_type"] == "Data"


# ============================================================
# 10. FILTER BY DATE
# ============================================================

def test_list_usage_by_date():
    setup = create_complete_setup()

    today = date.today()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_date=today,
        quantity=200,
    )

    response = client.get(
        f"/api/v1/usage?usage_date={today.isoformat()}",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) >= 1

    for item in data:
        assert item["usage_date"] == today.isoformat()


# ============================================================
# 11. CUSTOMER USAGE
# ============================================================

def test_customer_usage():
    setup = create_complete_setup()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        quantity=1000,
    )

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Voice",
        quantity=100,
    )

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="SMS",
        quantity=50,
    )

    response = client.get(
        f"/api/v1/usage/customer/{setup['customer']['id']}",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["customer_id"] == setup["customer"]["id"]
    assert data["data_usage_mb"] >= 1000
    assert data["voice_usage_minutes"] >= 100
    assert data["sms_usage"] >= 50


# ============================================================
# 12. SIM USAGE
# ============================================================

def test_sim_usage():
    setup = create_complete_setup()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        quantity=700,
    )

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Voice",
        quantity=60,
    )

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="SMS",
        quantity=40,
    )

    response = client.get(
        f"/api/v1/usage/sim/{setup['sim']['id']}",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["sim_id"] == setup["sim"]["id"]
    assert data["data_usage_mb"] >= 700
    assert data["voice_usage_minutes"] >= 60
    assert data["sms_usage"] >= 40


# ============================================================
# 13. DAILY USAGE
# ============================================================

def test_daily_usage():
    setup = create_complete_setup()

    today = date.today()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        usage_date=today,
        quantity=500,
    )

    response = client.get(
        f"/api/v1/usage/sim/{setup['sim']['id']}/daily"
        f"?usage_date={today.isoformat()}",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, (list, dict))


# ============================================================
# 14. MONTHLY USAGE
# ============================================================

def test_monthly_usage():
    setup = create_complete_setup()

    today = date.today()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        usage_date=today,
        quantity=800,
    )

    response = client.get(
        f"/api/v1/usage/sim/{setup['sim']['id']}/monthly"
        f"?year={today.year}&month={today.month}",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, (list, dict))


# ============================================================
# 15. PLAN UTILIZATION
# ============================================================

def test_plan_utilization():
    setup = create_complete_setup()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        quantity=1000,
    )

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Voice",
        quantity=200,
    )

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="SMS",
        quantity=100,
    )

    response = client.get(
        f"/api/v1/usage/sim/{setup['sim']['id']}/utilization",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["sim_id"] == setup["sim"]["id"]
    assert data["plan_id"] == setup["plan"]["id"]

    assert data["data_used_mb"] >= 1000
    assert data["voice_used_minutes"] >= 200
    assert data["sms_used"] >= 100

    assert data["data_limit_mb"] == 5000
    assert data["voice_limit_minutes"] == 1000
    assert data["sms_limit"] == 500


# ============================================================
# 16. DATA PERCENTAGE
# ============================================================

def test_data_usage_percentage():
    setup = create_complete_setup()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        quantity=1000,
    )

    response = client.get(
        f"/api/v1/usage/sim/{setup['sim']['id']}/utilization",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["data_percentage"] >= 0
    assert data["data_percentage"] <= 100


# ============================================================
# 17. VOICE PERCENTAGE
# ============================================================

def test_voice_usage_percentage():
    setup = create_complete_setup()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Voice",
        quantity=200,
    )

    response = client.get(
        f"/api/v1/usage/sim/{setup['sim']['id']}/utilization",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["voice_percentage"] >= 0
    assert data["voice_percentage"] <= 100


# ============================================================
# 18. SMS PERCENTAGE
# ============================================================

def test_sms_usage_percentage():
    setup = create_complete_setup()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="SMS",
        quantity=100,
    )

    response = client.get(
        f"/api/v1/usage/sim/{setup['sim']['id']}/utilization",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["sms_percentage"] >= 0
    assert data["sms_percentage"] <= 100


# ============================================================
# 19. REMAINING QUOTA
# ============================================================

def test_remaining_quota():
    setup = create_complete_setup()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        quantity=1000,
    )

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Voice",
        quantity=200,
    )

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="SMS",
        quantity=100,
    )

    response = client.get(
        f"/api/v1/usage/sim/{setup['sim']['id']}/remaining-quota",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["data_remaining_mb"] >= 0
    assert data["voice_remaining_minutes"] >= 0
    assert data["sms_remaining"] >= 0


# ============================================================
# 20. MULTIPLE RECORDS ARE AGGREGATED
# ============================================================

def test_multiple_usage_records_are_aggregated():
    setup = create_complete_setup()

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        quantity=100,
    )

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        quantity=200,
    )

    create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_type="Data",
        quantity=300,
    )

    response = client.get(
        f"/api/v1/usage/sim/{setup['sim']['id']}",
        headers=auth_headers(setup["admin_token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["data_usage_mb"] >= 600


# ============================================================
# 21. INVALID CUSTOMER
# ============================================================

def test_usage_invalid_customer():
    setup = create_complete_setup()

    response = create_usage(
        setup["admin_token"],
        999999999,
        setup["sim"]["id"],
        setup["subscription"]["id"],
        quantity=100,
    )

    assert response.status_code == 404


# ============================================================
# 22. INVALID SIM
# ============================================================

def test_usage_invalid_sim():
    setup = create_complete_setup()

    response = create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        999999999,
        setup["subscription"]["id"],
        quantity=100,
    )

    assert response.status_code == 404


# ============================================================
# 23. CUSTOMER / SIM MISMATCH
# ============================================================

def test_usage_customer_sim_mismatch():
    setup1 = create_complete_setup()
    setup2 = create_complete_setup()

    response = create_usage(
        setup1["admin_token"],
        setup2["customer"]["id"],
        setup1["sim"]["id"],
        setup1["subscription"]["id"],
        quantity=100,
    )

    assert response.status_code in (400, 404)


# ============================================================
# 24. INVALID SUBSCRIPTION
# ============================================================

def test_usage_invalid_subscription():
    setup = create_complete_setup()

    response = create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        999999999,
        quantity=100,
    )

    assert response.status_code == 404


# ============================================================
# 25. USAGE OUTSIDE SUBSCRIPTION
# ============================================================

def test_usage_outside_subscription_period():
    setup = create_complete_setup()

    old_date = date.today() - timedelta(days=365)

    response = create_usage(
        setup["admin_token"],
        setup["customer"]["id"],
        setup["sim"]["id"],
        setup["subscription"]["id"],
        usage_date=old_date,
        quantity=100,
    )

    assert response.status_code in (400, 422)