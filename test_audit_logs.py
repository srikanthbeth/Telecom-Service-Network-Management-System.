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


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def unique_email(prefix="audit"):
    return f"{prefix}_{uuid4().hex}@example.com"


def register_user(
    role="Customer",
    email=None,
):
    if email is None:
        email = unique_email(role.lower())

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Test {role}",
            "email": email,
            "phone": f"9{uuid4().int % 1000000000:09d}",
            "password": "Test@12345",
            "role": role,
        },
    )

    assert response.status_code in (
        200,
        201,
    ), response.text

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

    return response.json()


def get_token(email):
    login_response = login_user(email)

    return login_response["access_token"]


def test_audit_log_model_table_exists():
    with SessionLocal() as db:
        result = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'audit_logs'
                )
                """
            )
        )

        exists = result.scalar()

        assert exists is True


def test_create_audit_log_directly():
    from services.audit_log_service import AuditLogService

    user = register_user(
        role="Customer"
    )

    service = AuditLogService()

    with SessionLocal() as db:
        audit_log = service.create_log(
            db=db,
            user_id=user["id"],
            action="CUSTOMER_UPDATE",
            entity="Customer",
            entity_id=1,
            previous_value={
                "city": "Tirupati"
            },
            new_value={
                "city": "Chennai"
            },
        )

        assert audit_log.id is not None
        assert audit_log.user_id == user["id"]
        assert audit_log.action == "CUSTOMER_UPDATE"
        assert audit_log.entity == "Customer"
        assert audit_log.entity_id == 1
        assert "Tirupati" in audit_log.previous_value
        assert "Chennai" in audit_log.new_value


def test_get_audit_logs_requires_authentication():
    response = client.get(
        "/api/v1/audit-logs"
    )

    assert response.status_code == 401


def test_get_audit_logs():
    user = register_user(
        role="Customer"
    )

    token = get_token(
        user["email"]
    )

    from services.audit_log_service import AuditLogService

    service = AuditLogService()

    with SessionLocal() as db:
        service.create_log(
            db=db,
            user_id=user["id"],
            action="LOGIN_ACTIVITY",
            entity="User",
            entity_id=user["id"],
            previous_value=None,
            new_value={
                "status": "login_success"
            },
        )

    response = client.get(
        "/api/v1/audit-logs",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    audit_log = data[0]

    assert "id" in audit_log
    assert "user_id" in audit_log
    assert "action" in audit_log
    assert "entity" in audit_log
    assert "entity_id" in audit_log
    assert "timestamp" in audit_log
    assert "previous_value" in audit_log
    assert "new_value" in audit_log


def test_get_audit_log_by_id():
    user = register_user(
        role="Customer"
    )

    token = get_token(
        user["email"]
    )

    from services.audit_log_service import AuditLogService

    service = AuditLogService()

    with SessionLocal() as db:
        audit_log = service.create_log(
            db=db,
            user_id=user["id"],
            action="PLAN_CHANGE",
            entity="Plan",
            entity_id=10,
            previous_value={
                "plan_id": 5
            },
            new_value={
                "plan_id": 10
            },
        )

        audit_log_id = audit_log.id

    response = client.get(
        f"/api/v1/audit-logs/{audit_log_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == audit_log_id
    assert data["action"] == "PLAN_CHANGE"
    assert data["entity"] == "Plan"
    assert data["entity_id"] == 10


def test_audit_log_not_found():
    user = register_user(
        role="Customer"
    )

    token = get_token(
        user["email"]
    )

    response = client.get(
        "/api/v1/audit-logs/999999999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_audit_log_contains_previous_and_new_values():
    user = register_user(
        role="Customer"
    )

    from services.audit_log_service import AuditLogService

    service = AuditLogService()

    with SessionLocal() as db:
        audit_log = service.create_log(
            db=db,
            user_id=user["id"],
            action="SIM_ACTIVATION",
            entity="SIM",
            entity_id=25,
            previous_value={
                "status": "Available"
            },
            new_value={
                "status": "Active"
            },
        )

        assert audit_log.previous_value is not None
        assert audit_log.new_value is not None

        assert "Available" in (
            audit_log.previous_value
        )

        assert "Active" in (
            audit_log.new_value
        )


def test_audit_log_actions():
    from services.audit_log_service import AuditLogService

    user = register_user(
        role="Customer"
    )

    service = AuditLogService()

    actions = [
        "LOGIN_ACTIVITY",
        "CUSTOMER_UPDATE",
        "PLAN_CHANGE",
        "SUBSCRIPTION_CHANGE",
        "SIM_ACTIVATION",
        "SIM_SUSPENSION",
        "TICKET_UPDATE",
        "NETWORK_CHANGE",
        "ADMIN_ACTION",
    ]

    with SessionLocal() as db:
        for action in actions:
            service.create_log(
                db=db,
                user_id=user["id"],
                action=action,
                entity="TestEntity",
                entity_id=1,
                previous_value={
                    "old": "value"
                },
                new_value={
                    "new": "value"
                },
            )

        logs, total, total_pages = (
            service.get_all(
                db=db,
                page=1,
                page_size=20,
            )
        )

        assert total >= len(actions)

        stored_actions = {
            log.action
            for log in logs
        }

        for action in actions:
            assert action in stored_actions


def test_audit_log_filter_by_action():
    user = register_user(
        role="Customer"
    )

    from services.audit_log_service import AuditLogService

    service = AuditLogService()

    with SessionLocal() as db:
        service.create_log(
            db=db,
            user_id=user["id"],
            action="SIM_ACTIVATION",
            entity="SIM",
            entity_id=1,
        )

        service.create_log(
            db=db,
            user_id=user["id"],
            action="CUSTOMER_UPDATE",
            entity="Customer",
            entity_id=1,
        )

    token = get_token(
        user["email"]
    )

    response = client.get(
        "/api/v1/audit-logs",
        params={
            "action": "SIM_ACTIVATION"
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        item["action"] == "SIM_ACTIVATION"
        for item in data
    )


def test_audit_log_filter_by_entity():
    user = register_user(
        role="Customer"
    )

    from services.audit_log_service import AuditLogService

    service = AuditLogService()

    with SessionLocal() as db:
        service.create_log(
            db=db,
            user_id=user["id"],
            action="CUSTOMER_UPDATE",
            entity="Customer",
            entity_id=1,
        )

        service.create_log(
            db=db,
            user_id=user["id"],
            action="PLAN_CHANGE",
            entity="Plan",
            entity_id=1,
        )

    token = get_token(
        user["email"]
    )

    response = client.get(
        "/api/v1/audit-logs",
        params={
            "entity": "Customer"
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        item["entity"] == "Customer"
        for item in data
    )