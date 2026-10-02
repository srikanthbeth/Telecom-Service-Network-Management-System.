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


def create_customer(
    admin_token,
    customer_user_id,
):
    response = client.post(
        "/api/v1/customers",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
        json={
            "user_id": customer_user_id,
            "customer_number": (
                f"CUST-{uuid4().hex[:8]}"
            ),
            "address_line1": "Main Street",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "postal_code": "517501",
            "country": "India",
            "kyc_status": "Verified",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_plan(
    admin_token,
):
    response = client.post(
        "/api/v1/plans",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
        json={
            "plan_name": (
                f"SIM Plan-{uuid4().hex[:8]}"
            ),
            "description": "SIM test plan",
            "plan_type": "Prepaid",
            "validity_days": 28,
            "data_limit_mb": 10000,
            "voice_limit_minutes": 500,
            "sms_limit": 100,
            "price": 299.0,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_sim(
    admin_token,
    customer_id=None,
    plan_id=None,
    sim_type="Physical",
):
    response = client.post(
        "/api/v1/sims",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
        json={
            "sim_number": (
                f"SIM-{uuid4().hex[:12]}"
            ),
            "sim_type": sim_type,
            "customer_id": customer_id,
            "plan_id": plan_id,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_complete_setup():
    admin = register_user("Super Admin")
    admin_token = login(admin["email"])

    customer_user = register_user("Customer")

    customer = create_customer(
        admin_token,
        customer_user["id"],
    )

    plan = create_plan(
        admin_token,
    )

    return (
        admin,
        admin_token,
        customer,
        plan,
    )


def test_create_available_physical_sim():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    sim = create_sim(
        token,
        sim_type="Physical",
    )

    assert sim["sim_type"] == "Physical"
    assert sim["status"] == "Available"
    assert sim["customer_id"] is None
    assert sim["plan_id"] is None
    assert sim["activation_date"] is None


def test_create_esim():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    sim = create_sim(
        token,
        sim_type="eSIM",
    )

    assert sim["sim_type"] == "eSIM"
    assert sim["status"] == "Available"


def test_create_active_sim_with_customer_and_plan():

    (
        admin,
        token,
        customer,
        plan,
    ) = create_complete_setup()

    sim = create_sim(
        token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    assert sim["status"] == "Active"
    assert sim["customer_id"] == customer["id"]
    assert sim["plan_id"] == plan["id"]
    assert sim["activation_date"] is not None


def test_duplicate_sim_number_not_allowed():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    sim_number = (
        f"SIM-DUP-{uuid4().hex[:8]}"
    )

    first = client.post(
        "/api/v1/sims",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "sim_number": sim_number,
            "sim_type": "Physical",
        },
    )

    assert first.status_code == 201, first.text

    second = client.post(
        "/api/v1/sims",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "sim_number": sim_number,
            "sim_type": "Physical",
        },
    )

    assert second.status_code == 409


def test_invalid_customer_not_allowed():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    response = client.post(
        "/api/v1/sims",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "sim_number": (
                f"SIM-{uuid4().hex[:8]}"
            ),
            "sim_type": "Physical",
            "customer_id": 999999,
        },
    )

    assert response.status_code == 404


def test_invalid_plan_not_allowed():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    response = client.post(
        "/api/v1/sims",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "sim_number": (
                f"SIM-{uuid4().hex[:8]}"
            ),
            "sim_type": "Physical",
            "plan_id": 999999,
        },
    )

    assert response.status_code == 404


def test_inactive_plan_cannot_be_assigned():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    plan = create_plan(token)

    deactivate = client.patch(
        f"/api/v1/plans/{plan['id']}/deactivate",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert deactivate.status_code == 200

    response = client.post(
        "/api/v1/sims",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "sim_number": (
                f"SIM-{uuid4().hex[:8]}"
            ),
            "sim_type": "Physical",
            "plan_id": plan["id"],
        },
    )

    assert response.status_code == 400


def test_get_sim():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    sim = create_sim(token)

    response = client.get(
        f"/api/v1/sims/{sim['id']}",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["id"] == sim["id"]
    assert result["sim_number"] == sim["sim_number"]


def test_update_sim():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    sim = create_sim(
        token,
        sim_type="Physical",
    )

    response = client.patch(
        f"/api/v1/sims/{sim['id']}",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "sim_type": "eSIM",
        },
    )

    assert response.status_code == 200

    updated = response.json()

    assert updated["sim_type"] == "eSIM"


def test_activate_sim():

    (
        admin,
        token,
        customer,
        plan,
    ) = create_complete_setup()

    sim = create_sim(token)

    response = client.patch(
        f"/api/v1/sims/{sim['id']}/activate",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 400

    update = client.patch(
        f"/api/v1/sims/{sim['id']}",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "customer_id": customer["id"],
            "plan_id": plan["id"],
        },
    )

    assert update.status_code == 200

    response = client.patch(
        f"/api/v1/sims/{sim['id']}/activate",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    activated = response.json()

    assert activated["status"] == "Active"
    assert activated["customer_id"] == customer["id"]
    assert activated["plan_id"] == plan["id"]
    assert activated["activation_date"] is not None


def test_suspend_sim():

    (
        admin,
        token,
        customer,
        plan,
    ) = create_complete_setup()

    sim = create_sim(
        token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    response = client.patch(
        f"/api/v1/sims/{sim['id']}/suspend",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Suspended"


def test_mark_sim_lost():

    (
        admin,
        token,
        customer,
        plan,
    ) = create_complete_setup()

    sim = create_sim(
        token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    response = client.patch(
        f"/api/v1/sims/{sim['id']}/lost",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Lost"


def test_block_sim():

    (
        admin,
        token,
        customer,
        plan,
    ) = create_complete_setup()

    sim = create_sim(
        token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    response = client.patch(
        f"/api/v1/sims/{sim['id']}/block",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Blocked"


def test_deactivate_sim():

    (
        admin,
        token,
        customer,
        plan,
    ) = create_complete_setup()

    sim = create_sim(
        token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    response = client.patch(
        f"/api/v1/sims/{sim['id']}/deactivate",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Deactivated"


def test_search_sims():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    sim_number = (
        f"SEARCH-SIM-{uuid4().hex[:8]}"
    )

    response = client.post(
        "/api/v1/sims",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "sim_number": sim_number,
            "sim_type": "Physical",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/sims",
        params={
            "search": "SEARCH-SIM"
        },
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    sims = response.json()

    assert len(sims) >= 1

    assert any(
        "SEARCH-SIM" in sim["sim_number"]
        for sim in sims
    )


def test_filter_sims_by_type():

    admin = register_user("Super Admin")
    token = login(admin["email"])

    create_sim(
        token,
        sim_type="eSIM",
    )

    response = client.get(
        "/api/v1/sims",
        params={
            "sim_type": "eSIM"
        },
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    sims = response.json()

    assert len(sims) >= 1

    assert all(
        sim["sim_type"] == "eSIM"
        for sim in sims
    )


def test_filter_sims_by_status():

    (
        admin,
        token,
        customer,
        plan,
    ) = create_complete_setup()

    sim = create_sim(
        token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    client.patch(
        f"/api/v1/sims/{sim['id']}/suspend",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    response = client.get(
        "/api/v1/sims",
        params={
            "status": "Suspended"
        },
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    sims = response.json()

    assert len(sims) >= 1

    assert all(
        sim["status"] == "Suspended"
        for sim in sims
    )


def test_filter_sims_by_customer():

    (
        admin,
        token,
        customer,
        plan,
    ) = create_complete_setup()

    create_sim(
        token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    response = client.get(
        "/api/v1/sims",
        params={
            "customer_id": customer["id"]
        },
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    sims = response.json()

    assert len(sims) >= 1

    assert all(
        sim["customer_id"] == customer["id"]
        for sim in sims
    )


def test_sim_replacement():

    (
        admin,
        token,
        customer,
        plan,
    ) = create_complete_setup()

    old_sim = create_sim(
        token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    new_sim = create_sim(
        token
    )

    response = client.post(
        f"/api/v1/sims/{old_sim['id']}/replace",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "new_sim_id": new_sim["id"],
            "reason": "SIM lost",
        },
    )

    assert response.status_code == 200

    replacement = response.json()

    assert replacement["id"] == new_sim["id"]
    assert replacement["status"] == "Active"
    assert replacement["customer_id"] == customer["id"]
    assert replacement["plan_id"] == plan["id"]

    old_response = client.get(
        f"/api/v1/sims/{old_sim['id']}",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert old_response.status_code == 200
    assert (
        old_response.json()["status"]
        == "Deactivated"
    )


def test_replacement_history():

    (
        admin,
        token,
        customer,
        plan,
    ) = create_complete_setup()

    old_sim = create_sim(
        token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    new_sim = create_sim(
        token
    )

    response = client.post(
        f"/api/v1/sims/{old_sim['id']}/replace",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "new_sim_id": new_sim["id"],
            "reason": "SIM damaged",
        },
    )

    assert response.status_code == 200

    response = client.get(
        f"/api/v1/sims/{old_sim['id']}/replacement-history",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    history = response.json()

    assert len(history) == 1

    assert history[0]["old_sim_id"] == old_sim["id"]
    assert history[0]["new_sim_id"] == new_sim["id"]
    assert history[0]["customer_id"] == customer["id"]
    assert history[0]["reason"] == "SIM damaged"
    assert history[0]["replaced_by"] == admin["id"]


def test_customer_can_view_sims():

    (
        admin,
        admin_token,
        customer,
        plan,
    ) = create_complete_setup()

    create_sim(
        admin_token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    customer_user = client.get(
        "/api/v1/customers",
        headers={
            "Authorization": (
                f"Bearer {admin_token}"
            )
        },
    )

    assert customer_user.status_code == 200

    customer_users = register_user("Customer")
    customer_token = login(
        customer_users["email"]
    )

    response = client.get(
        "/api/v1/sims",
        headers={
            "Authorization": (
                f"Bearer {customer_token}"
            )
        },
    )

    assert response.status_code == 200


def test_customer_cannot_create_sim():

    customer = register_user("Customer")
    token = login(customer["email"])

    response = client.post(
        "/api/v1/sims",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "sim_number": (
                f"SIM-CUSTOMER-{uuid4().hex[:8]}"
            ),
            "sim_type": "Physical",
        },
    )

    assert response.status_code == 403


def test_customer_cannot_replace_sim():

    (
        admin,
        admin_token,
        customer,
        plan,
    ) = create_complete_setup()

    old_sim = create_sim(
        admin_token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    new_sim = create_sim(
        admin_token
    )

    customer_user = register_user("Customer")
    customer_token = login(
        customer_user["email"]
    )

    response = client.post(
        f"/api/v1/sims/{old_sim['id']}/replace",
        headers={
            "Authorization": (
                f"Bearer {customer_token}"
            )
        },
        json={
            "new_sim_id": new_sim["id"],
            "reason": "Unauthorized replacement",
        },
    )

    assert response.status_code == 403


def test_replacement_requires_available_new_sim():

    (
        admin,
        token,
        customer,
        plan,
    ) = create_complete_setup()

    old_sim = create_sim(
        token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    new_sim = create_sim(
        token,
        customer_id=customer["id"],
        plan_id=plan["id"],
    )

    response = client.post(
        f"/api/v1/sims/{old_sim['id']}/replace",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "new_sim_id": new_sim["id"],
            "reason": "Replacement",
        },
    )

    assert response.status_code == 400