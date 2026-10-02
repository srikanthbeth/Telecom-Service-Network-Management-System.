import os
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "telecom_service_network_test"
)

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from db.database import Base, SessionLocal, engine
from main import app

from models.customer import Customer
from models.plan import Plan
from models.sim import SIM
from models.subscription import Subscription
from models.tower import Tower
from models.user import User

from utils.enums import (
    
    KYCStatus,
    PlanStatus,
    PlanType,
    SIMStatus,
    SIMType,
    SubscriptionStatus,
    UserRole,
)


client = TestClient(app)


# ============================================================
# SETUP / TEARDOWN
# ============================================================

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


# ============================================================
# DATABASE HELPER
# ============================================================

def get_db() -> Session:
    return SessionLocal()


def unique_value(prefix="TEST"):
    return f"{prefix}-{uuid4().hex[:8]}"


# ============================================================
# CREATE TEST DATA DIRECTLY IN DATABASE
# ============================================================

def create_user(
    db,
    role=UserRole.CUSTOMER,
    email=None,
):
    user = User(
        full_name=f"User-{uuid4().hex[:8]}",
        email=email or f"{uuid4().hex[:8]}@example.com",
        phone=f"9{uuid4().int % 10_000_000_000:010d}",
        password_hash="test-password",
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def create_customer(
    db: Session,
):
    user = create_user(
        db,
        UserRole.CUSTOMER,
    )

    customer = Customer(
        user_id=user.id,
        customer_number=unique_value("CUST"),
        address_line1="Main Road",
        city="Tirupati",
        state="Andhra Pradesh",
        postal_code="517501",
        country="India",
        kyc_status=KYCStatus.VERIFIED,
    )

    db.add(customer)
    db.flush()

    return customer


def create_plan(
    db: Session,
):
    plan = Plan(
        plan_name=unique_value("Plan"),
        description="Test telecom plan",
        plan_type=PlanType.POSTPAID,
        price=499.0,
        validity_days=30,
        status=PlanStatus.ACTIVE,
    )

    db.add(plan)
    db.flush()

    return plan


def create_tower(
    db: Session,
):
    tower = Tower(
        tower_code=unique_value("TOWER"),
        tower_name=unique_value("Tower"),
        tower_type="Macro",
        latitude=13.6288,
        longitude=79.4192,
        address="Tirupati",
        coverage_area=25.5,
        capacity=5000,
        status="Active",
    )

    db.add(tower)
    db.flush()

    return tower


def create_sim(
    db: Session,
    customer_id: int,
    plan_id: int,
    tower_id: int,
):
    sim = SIM(
        sim_number=unique_value("SIM"),
        sim_type=SIMType.PHYSICAL,
        status=SIMStatus.ACTIVE,
        activation_date=date.today(),
        customer_id=customer_id,
        plan_id=plan_id,
        tower_id=tower_id,
    )

    db.add(sim)
    db.flush()

    return sim


def create_subscription(
    db: Session,
    customer_id: int,
    sim_id: int,
    plan_id: int,
    status=SubscriptionStatus.ACTIVE,
):
    today = date.today()

    subscription = Subscription(
        customer_id=customer_id,
        sim_id=sim_id,
        plan_id=plan_id,
        start_date=today,
        end_date=today + timedelta(days=30),
        status=status,
    )

    db.add(subscription)
    db.flush()

    return subscription


def create_complete_setup(
    db: Session,
):
    customer = create_customer(db)
    plan = create_plan(db)
    tower = create_tower(db)

    sim = create_sim(
        db,
        customer_id=customer.id,
        plan_id=plan.id,
        tower_id=tower.id,
    )

    subscription = create_subscription(
        db,
        customer_id=customer.id,
        sim_id=sim.id,
        plan_id=plan.id,
    )

    db.commit()

    return {
        "customer": customer,
        "plan": plan,
        "tower": tower,
        "sim": sim,
        "subscription": subscription,
    }


# ============================================================
# OUTAGE HELPER
# ============================================================

def create_outage(
    tower_ids,
    outage_code=None,
    severity="High",
    outage_type="Network Failure",
):
    start_time = datetime.now(
        timezone.utc
    ).replace(microsecond=0)

    expected_resolution = (
        start_time + timedelta(hours=2)
    )

    return client.post(
        "/api/v1/outages",
        json={
            "outage_code": (
                outage_code
                or unique_value("OUT")
            ),
            "outage_type": outage_type,
            "description": "Network outage test",
            "severity": severity,
            "start_time": start_time.isoformat(),
            "expected_resolution": (
                expected_resolution.isoformat()
            ),
            "tower_ids": tower_ids,
        },
    )


# ============================================================
# CREATE OUTAGE
# ============================================================

def test_create_outage():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        response = create_outage(
            [setup["tower"].id]
        )

        assert response.status_code == 201, response.text

        data = response.json()

        assert data["outage_code"]
        assert data["outage_type"] == "Network Failure"
        assert data["severity"] == "High"

        assert (
            setup["tower"].id
            in data["tower_ids"]
        )

    finally:
        db.close()


def test_create_outage_with_low_severity():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        response = create_outage(
            [setup["tower"].id],
            severity="Low",
        )

        assert response.status_code == 201
        assert response.json()["severity"] == "Low"

    finally:
        db.close()


def test_create_outage_with_medium_severity():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        response = create_outage(
            [setup["tower"].id],
            severity="Medium",
        )

        assert response.status_code == 201
        assert response.json()["severity"] == "Medium"

    finally:
        db.close()


def test_create_outage_with_high_severity():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        response = create_outage(
            [setup["tower"].id],
            severity="High",
        )

        assert response.status_code == 201
        assert response.json()["severity"] == "High"

    finally:
        db.close()


def test_create_outage_with_critical_severity():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        response = create_outage(
            [setup["tower"].id],
            severity="Critical",
        )

        assert response.status_code == 201
        assert response.json()["severity"] == "Critical"

    finally:
        db.close()


# ============================================================
# OUTAGE TYPE
# ============================================================

def test_create_different_outage_type():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        response = create_outage(
            [setup["tower"].id],
            outage_type="Power Failure",
        )

        assert response.status_code == 201
        assert (
            response.json()["outage_type"]
            == "Power Failure"
        )

    finally:
        db.close()


def test_outage_type_filter():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        create_outage(
            [setup["tower"].id],
            outage_type="Fiber Failure",
        )

        response = client.get(
            "/api/v1/outages",
            params={
                "outage_type": "Fiber Failure"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert any(
            item["outage_type"]
            == "Fiber Failure"
            for item in data
        )

    finally:
        db.close()


# ============================================================
# TOWER MAPPING
# ============================================================

def test_outage_contains_affected_tower():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        tower_id = setup["tower"].id

        response = create_outage(
            [tower_id]
        )

        assert response.status_code == 201

        assert (
            tower_id
            in response.json()["tower_ids"]
        )

    finally:
        db.close()


def test_outage_can_have_multiple_towers():
    db = get_db()

    try:
        tower1 = create_tower(db)
        tower2 = create_tower(db)

        db.commit()

        response = create_outage(
            [
                tower1.id,
                tower2.id,
            ]
        )

        assert response.status_code == 201

        data = response.json()

        assert tower1.id in data["tower_ids"]
        assert tower2.id in data["tower_ids"]

    finally:
        db.close()


def test_outage_fails_for_nonexistent_tower():
    response = create_outage(
        [999999]
    )

    assert response.status_code == 404


def test_outage_requires_tower():
    start_time = datetime.now(
        timezone.utc
    ).replace(microsecond=0)

    response = client.post(
        "/api/v1/outages",
        json={
            "outage_code": unique_value("OUT"),
            "outage_type": "Network Failure",
            "description": "No tower",
            "severity": "High",
            "start_time": start_time.isoformat(),
            "expected_resolution": (
                start_time
                + timedelta(hours=2)
            ).isoformat(),
            "tower_ids": [],
        },
    )

    assert response.status_code == 422


# ============================================================
# AUTOMATIC AFFECTED CUSTOMERS
# ============================================================

def test_affected_customer_is_identified_automatically():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        response = create_outage(
            [setup["tower"].id]
        )

        assert response.status_code == 201

        data = response.json()

        assert (
            setup["customer"].id
            in data["affected_customer_ids"]
        )

    finally:
        db.close()


def test_affected_customers_endpoint():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        create_response = create_outage(
            [setup["tower"].id]
        )

        assert create_response.status_code == 201

        outage_id = create_response.json()["id"]

        response = client.get(
            f"/api/v1/outages/"
            f"{outage_id}/affected-customers"
        )

        assert response.status_code == 200

        data = response.json()

        assert any(
            item["customer_id"]
            == setup["customer"].id
            for item in data
        )

    finally:
        db.close()


def test_multiple_customers_are_identified():
    db = get_db()

    try:
        tower = create_tower(db)
        plan = create_plan(db)

        customer1 = create_customer(db)
        customer2 = create_customer(db)

        sim1 = create_sim(
            db,
            customer1.id,
            plan.id,
            tower.id,
        )

        sim2 = create_sim(
            db,
            customer2.id,
            plan.id,
            tower.id,
        )

        create_subscription(
            db,
            customer1.id,
            sim1.id,
            plan.id,
        )

        create_subscription(
            db,
            customer2.id,
            sim2.id,
            plan.id,
        )

        db.commit()

        response = create_outage(
            [tower.id]
        )

        assert response.status_code == 201

        affected = response.json()[
            "affected_customer_ids"
        ]

        assert customer1.id in affected
        assert customer2.id in affected

    finally:
        db.close()


def test_cancelled_subscription_is_not_affected():
    db = get_db()

    try:
        tower = create_tower(db)
        plan = create_plan(db)
        customer = create_customer(db)

        sim = create_sim(
            db,
            customer.id,
            plan.id,
            tower.id,
        )

        create_subscription(
            db,
            customer.id,
            sim.id,
            plan.id,
            SubscriptionStatus.CANCELLED,
        )

        db.commit()

        response = create_outage(
            [tower.id]
        )

        assert response.status_code == 201

        affected = response.json()[
            "affected_customer_ids"
        ]

        assert customer.id not in affected

    finally:
        db.close()


# ============================================================
# GET
# ============================================================

def test_get_outage():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        create_response = create_outage(
            [setup["tower"].id]
        )

        assert create_response.status_code == 201

        outage_id = create_response.json()["id"]

        response = client.get(
            f"/api/v1/outages/{outage_id}"
        )

        assert response.status_code == 200
        assert response.json()["id"] == outage_id

    finally:
        db.close()


def test_get_nonexistent_outage():
    response = client.get(
        "/api/v1/outages/999999"
    )

    assert response.status_code == 404


# ============================================================
# LIST
# ============================================================

def test_list_outages():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        create_outage(
            [setup["tower"].id]
        )

        response = client.get(
            "/api/v1/outages"
        )

        assert response.status_code == 200
        assert isinstance(
            response.json(),
            list,
        )

    finally:
        db.close()


def test_filter_by_severity():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        create_outage(
            [setup["tower"].id],
            severity="Critical",
        )

        response = client.get(
            "/api/v1/outages",
            params={
                "severity": "Critical"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert all(
            item["severity"] == "Critical"
            for item in data
        )

    finally:
        db.close()


# ============================================================
# DUPLICATE
# ============================================================

def test_duplicate_outage_code():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        code = unique_value("DUP")

        first = create_outage(
            [setup["tower"].id],
            outage_code=code,
        )

        assert first.status_code == 201

        second = create_outage(
            [setup["tower"].id],
            outage_code=code,
        )

        assert second.status_code == 409

    finally:
        db.close()


# ============================================================
# UPDATE
# ============================================================

def test_update_outage():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        create_response = create_outage(
            [setup["tower"].id]
        )

        assert create_response.status_code == 201

        outage_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/outages/{outage_id}",
            json={
                "outage_type": "Equipment Failure",
                "description": "Updated description",
                "severity": "Critical",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert (
            data["outage_type"]
            == "Equipment Failure"
        )

        assert (
            data["description"]
            == "Updated description"
        )

        assert data["severity"] == "Critical"

    finally:
        db.close()


def test_update_nonexistent_outage():
    response = client.put(
        "/api/v1/outages/999999",
        json={
            "severity": "High"
        },
    )

    assert response.status_code == 404


# ============================================================
# RESOLVE
# ============================================================

def test_resolve_outage():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        create_response = create_outage(
            [setup["tower"].id]
        )

        assert create_response.status_code == 201

        outage_id = create_response.json()["id"]

        resolution_time = (
            datetime.now(timezone.utc)
            + timedelta(hours=3)
        ).replace(microsecond=0)

        response = client.patch(
            f"/api/v1/outages/"
            f"{outage_id}/resolve",
            json={
                "actual_resolution":
                    resolution_time.isoformat()
            },
        )

        assert response.status_code == 200

        assert (
            response.json()["actual_resolution"]
            is not None
        )

    finally:
        db.close()


def test_resolve_outage_without_time():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        create_response = create_outage(
            [setup["tower"].id]
        )

        outage_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/outages/"
            f"{outage_id}/resolve",
            json={},
        )

        assert response.status_code == 200

        assert (
            response.json()["actual_resolution"]
            is not None
        )

    finally:
        db.close()


def test_resolution_before_start_time_fails():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        start_time = datetime.now(
            timezone.utc
        ).replace(microsecond=0)

        create_response = client.post(
            "/api/v1/outages",
            json={
                "outage_code": unique_value("OUT"),
                "outage_type": "Network Failure",
                "description": "Resolution validation",
                "severity": "High",
                "start_time": start_time.isoformat(),
                "expected_resolution": (
                    start_time
                    + timedelta(hours=2)
                ).isoformat(),
                "tower_ids": [
                    setup["tower"].id
                ],
            },
        )

        assert create_response.status_code == 201

        outage_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/outages/"
            f"{outage_id}/resolve",
            json={
                "actual_resolution": (
                    start_time
                    - timedelta(hours=1)
                ).isoformat()
            },
        )

        assert response.status_code == 400

    finally:
        db.close()


# ============================================================
# VALIDATION
# ============================================================

def test_invalid_severity():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        response = create_outage(
            [setup["tower"].id],
            severity="Invalid Severity",
        )

        assert response.status_code == 422

    finally:
        db.close()


def test_missing_outage_code():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        start_time = datetime.now(
            timezone.utc
        ).replace(microsecond=0)

        response = client.post(
            "/api/v1/outages",
            json={
                "outage_type": "Network Failure",
                "description": "Missing code",
                "severity": "High",
                "start_time": start_time.isoformat(),
                "expected_resolution": (
                    start_time
                    + timedelta(hours=2)
                ).isoformat(),
                "tower_ids": [
                    setup["tower"].id
                ],
            },
        )

        assert response.status_code == 422

    finally:
        db.close()


def test_missing_outage_type():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        start_time = datetime.now(
            timezone.utc
        ).replace(microsecond=0)

        response = client.post(
            "/api/v1/outages",
            json={
                "outage_code": unique_value("OUT"),
                "severity": "High",
                "start_time": start_time.isoformat(),
                "tower_ids": [
                    setup["tower"].id
                ],
            },
        )

        assert response.status_code == 422

    finally:
        db.close()


def test_missing_severity():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        start_time = datetime.now(
            timezone.utc
        ).replace(microsecond=0)

        response = client.post(
            "/api/v1/outages",
            json={
                "outage_code": unique_value("OUT"),
                "outage_type": "Network Failure",
                "start_time": start_time.isoformat(),
                "tower_ids": [
                    setup["tower"].id
                ],
            },
        )

        assert response.status_code == 422

    finally:
        db.close()


def test_missing_start_time():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        response = client.post(
            "/api/v1/outages",
            json={
                "outage_code": unique_value("OUT"),
                "outage_type": "Network Failure",
                "severity": "High",
                "tower_ids": [
                    setup["tower"].id
                ],
            },
        )

        assert response.status_code == 422

    finally:
        db.close()


# ============================================================
# DELETE
# ============================================================

def test_delete_outage():
    db = get_db()

    try:
        setup = create_complete_setup(db)

        create_response = create_outage(
            [setup["tower"].id]
        )

        assert create_response.status_code == 201

        outage_id = create_response.json()["id"]

        response = client.delete(
            f"/api/v1/outages/{outage_id}"
        )

        assert response.status_code == 204

        get_response = client.get(
            f"/api/v1/outages/{outage_id}"
        )

        assert get_response.status_code == 404

    finally:
        db.close()


def test_delete_nonexistent_outage():
    response = client.delete(
        "/api/v1/outages/999999"
    )

    assert response.status_code == 404