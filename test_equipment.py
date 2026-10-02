
import os
from datetime import date, datetime

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


def create_equipment(
    equipment_code="EQ-001",
    equipment_name="Main Router",
    equipment_type="Router",
    tower_id=None,
    network_status="Online",
    health_status="Healthy",
):
    response = client.post(
        "/api/v1/equipment",
        json={
            "equipment_code": equipment_code,
            "equipment_name": equipment_name,
            "equipment_type": equipment_type,
            "manufacturer": "Cisco",
            "model_number": "ISR-4000",
            "serial_number": f"SN-{equipment_code}",
            "tower_id": tower_id,
            "location": "Network Operations Center",
            "installation_date": "2026-01-15",
            "maintenance_schedule": "2026-12-15",
            "cpu_usage": 35.5,
            "memory_usage": 48.2,
            "network_status": network_status,
            "health_status": health_status,
            "last_heartbeat": "2026-09-28T10:30:00",
            "downtime_minutes": 0,
            "description": "Network equipment test record",
        },
    )

    return response


def test_create_router():
    response = create_equipment()

    assert response.status_code == 201

    data = response.json()

    assert data["equipment_code"] == "EQ-001"
    assert data["equipment_name"] == "Main Router"
    assert data["equipment_type"] == "Router"
    assert data["network_status"] == "Online"
    assert data["health_status"] == "Healthy"


def test_create_switch():
    response = create_equipment(
        equipment_code="EQ-SW-001",
        equipment_name="Core Switch",
        equipment_type="Switch",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["equipment_type"] == "Switch"


def test_create_base_station():
    response = create_equipment(
        equipment_code="EQ-BS-001",
        equipment_name="Base Station",
        equipment_type="Base Station",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["equipment_type"] == "Base Station"


def test_create_network_device():
    response = create_equipment(
        equipment_code="EQ-ND-001",
        equipment_name="Network Device",
        equipment_type="Network Device",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["equipment_type"] == "Network Device"


def test_get_equipment():
    response = client.get("/api/v1/equipment/1")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["equipment_code"] == "EQ-001"


def test_get_nonexistent_equipment():
    response = client.get("/api/v1/equipment/99999")

    assert response.status_code == 404


def test_duplicate_equipment_code():
    response = create_equipment(
        equipment_code="EQ-001",
        equipment_name="Duplicate Router",
    )

    assert response.status_code == 409


def test_list_equipment():
    response = client.get(
        "/api/v1/equipment"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 4


def test_filter_by_equipment_type():
    response = client.get(
        "/api/v1/equipment",
        params={
            "equipment_type": "Router"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for equipment in data:
        assert equipment["equipment_type"] == "Router"


def test_filter_by_network_status():
    response = client.get(
        "/api/v1/equipment",
        params={
            "network_status": "Online"
        },
    )

    assert response.status_code == 200

    data = response.json()

    for equipment in data:
        assert equipment["network_status"] == "Online"


def test_filter_by_health_status():
    response = client.get(
        "/api/v1/equipment",
        params={
            "health_status": "Healthy"
        },
    )

    assert response.status_code == 200

    data = response.json()

    for equipment in data:
        assert equipment["health_status"] == "Healthy"


def test_search_equipment():
    response = client.get(
        "/api/v1/equipment",
        params={
            "search": "Router"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1


def test_update_equipment():
    response = client.put(
        "/api/v1/equipment/1",
        json={
            "equipment_name": "Updated Main Router",
            "manufacturer": "Huawei",
            "model_number": "NE8000",
            "location": "Updated NOC",
            "cpu_usage": 60.0,
            "memory_usage": 70.0,
            "downtime_minutes": 15,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["equipment_name"] == "Updated Main Router"
    assert data["manufacturer"] == "Huawei"
    assert data["cpu_usage"] == 60.0
    assert data["memory_usage"] == 70.0
    assert data["downtime_minutes"] == 15


def test_update_network_status_offline():
    response = client.patch(
        "/api/v1/equipment/1/status",
        json={
            "network_status": "Offline"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["network_status"] == "Offline"


def test_update_network_status_maintenance():
    response = client.patch(
        "/api/v1/equipment/1/status",
        json={
            "network_status": "Maintenance"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["network_status"] == "Maintenance"


def test_update_network_status_degraded():
    response = client.patch(
        "/api/v1/equipment/1/status",
        json={
            "network_status": "Degraded"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["network_status"] == "Degraded"


def test_update_network_status_online():
    response = client.patch(
        "/api/v1/equipment/1/status",
        json={
            "network_status": "Online"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["network_status"] == "Online"


def test_update_health_warning():
    response = client.patch(
        "/api/v1/equipment/1/health",
        json={
            "health_status": "Warning"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["health_status"] == "Warning"


def test_update_health_critical():
    response = client.patch(
        "/api/v1/equipment/1/health",
        json={
            "health_status": "Critical"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["health_status"] == "Critical"


def test_update_health_healthy():
    response = client.patch(
        "/api/v1/equipment/1/health",
        json={
            "health_status": "Healthy"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["health_status"] == "Healthy"


def test_invalid_equipment_type():
    response = create_equipment(
        equipment_code="EQ-INVALID-TYPE",
        equipment_name="Invalid Equipment",
        equipment_type="Invalid Type",
    )

    assert response.status_code == 422


def test_invalid_network_status():
    response = client.patch(
        "/api/v1/equipment/1/status",
        json={
            "network_status": "Invalid Status"
        },
    )

    assert response.status_code == 422


def test_invalid_health_status():
    response = client.patch(
        "/api/v1/equipment/1/health",
        json={
            "health_status": "Invalid Health"
        },
    )

    assert response.status_code == 422


def test_invalid_cpu_usage():
    response = create_equipment(
        equipment_code="EQ-CPU-INVALID",
    )

    assert response.status_code == 201

    equipment_id = response.json()["id"]

    response = client.put(
        f"/api/v1/equipment/{equipment_id}",
        json={
            "cpu_usage": 101,
        },
    )

    assert response.status_code == 422


def test_invalid_memory_usage():
    response = create_equipment(
        equipment_code="EQ-MEM-INVALID",
    )

    assert response.status_code == 201

    equipment_id = response.json()["id"]

    response = client.put(
        f"/api/v1/equipment/{equipment_id}",
        json={
            "memory_usage": 101,
        },
    )

    assert response.status_code == 422


def test_negative_cpu_usage():
    response = create_equipment(
        equipment_code="EQ-CPU-NEGATIVE",
    )

    assert response.status_code == 201

    equipment_id = response.json()["id"]

    response = client.put(
        f"/api/v1/equipment/{equipment_id}",
        json={
            "cpu_usage": -1,
        },
    )

    assert response.status_code == 422


def test_negative_memory_usage():
    response = create_equipment(
        equipment_code="EQ-MEM-NEGATIVE",
    )

    assert response.status_code == 201

    equipment_id = response.json()["id"]

    response = client.put(
        f"/api/v1/equipment/{equipment_id}",
        json={
            "memory_usage": -1,
        },
    )

    assert response.status_code == 422


def test_negative_downtime():
    response = create_equipment(
        equipment_code="EQ-DOWN-NEGATIVE",
    )

    assert response.status_code == 201

    equipment_id = response.json()["id"]

    response = client.put(
        f"/api/v1/equipment/{equipment_id}",
        json={
            "downtime_minutes": -10,
        },
    )

    assert response.status_code == 422


def test_response_contains_monitoring_fields():
    response = client.get(
        "/api/v1/equipment/1"
    )

    assert response.status_code == 200

    data = response.json()

    assert "cpu_usage" in data
    assert "memory_usage" in data
    assert "network_status" in data
    assert "health_status" in data
    assert "last_heartbeat" in data
    assert "downtime_minutes" in data


def test_response_contains_maintenance_fields():
    response = client.get(
        "/api/v1/equipment/1"
    )

    assert response.status_code == 200

    data = response.json()

    assert "installation_date" in data
    assert "maintenance_schedule" in data
    assert "location" in data


def test_delete_equipment():
    response = create_equipment(
        equipment_code="EQ-DELETE-001",
        equipment_name="Equipment To Delete",
    )

    assert response.status_code == 201

    equipment_id = response.json()["id"]

    response = client.delete(
        f"/api/v1/equipment/{equipment_id}"
    )

    assert response.status_code == 204

    response = client.get(
        f"/api/v1/equipment/{equipment_id}"
    )

    assert response.status_code == 404

