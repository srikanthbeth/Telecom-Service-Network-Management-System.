
import os

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "telecom_service_network_test"
)

from fastapi.testclient import TestClient

from db.database import Base, engine
from main import app


client = TestClient(app)


# =========================================================
# SETUP
# =========================================================

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


# =========================================================
# HELPER
# =========================================================

def create_tower(
    tower_code="TOWER-001",
    tower_name="Central Tower",
    tower_type="Macro",
    latitude=13.6288,
    longitude=79.4192,
    address="Tirupati",
    coverage_area=25.5,
    capacity=5000,
    status="Active",
):
    return client.post(
        "/api/v1/towers",
        json={
            "tower_code": tower_code,
            "tower_name": tower_name,
            "tower_type": tower_type,
            "latitude": latitude,
            "longitude": longitude,
            "address": address,
            "coverage_area": coverage_area,
            "capacity": capacity,
            "status": status,
        },
    )


# =========================================================
# CREATE
# =========================================================

def test_create_tower():
    response = create_tower()

    assert response.status_code == 201

    data = response.json()

    assert data["tower_code"] == "TOWER-001"
    assert data["tower_name"] == "Central Tower"
    assert data["tower_type"] == "Macro"
    assert data["latitude"] == 13.6288
    assert data["longitude"] == 79.4192
    assert data["address"] == "Tirupati"
    assert data["coverage_area"] == 25.5
    assert data["capacity"] == 5000
    assert data["status"] == "Active"


# =========================================================
# GET
# =========================================================

def test_get_tower():
    response = client.get(
        "/api/v1/towers/1"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["tower_code"] == "TOWER-001"


def test_get_nonexistent_tower():
    response = client.get(
        "/api/v1/towers/99999"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Tower not found"


# =========================================================
# DUPLICATE
# =========================================================

def test_duplicate_tower_code():
    response = create_tower(
        tower_code="TOWER-001",
        tower_name="Duplicate Tower",
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]
        == "Tower code already exists"
    )


# =========================================================
# CREATE SECOND TOWER
# =========================================================

def test_create_second_tower():
    response = create_tower(
        tower_code="TOWER-002",
        tower_name="Micro Tower",
        tower_type="Micro",
        latitude=13.6300,
        longitude=79.4200,
        address="Renigunta",
        coverage_area=10.0,
        capacity=1000,
        status="Active",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["tower_code"] == "TOWER-002"
    assert data["tower_type"] == "Micro"


# =========================================================
# LIST
# =========================================================

def test_list_towers():
    response = client.get(
        "/api/v1/towers"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 2


# =========================================================
# FILTER BY STATUS
# =========================================================

def test_filter_towers_by_status():
    response = client.get(
        "/api/v1/towers?status=Active"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for tower in data:
        assert tower["status"] == "Active"


# =========================================================
# FILTER BY TYPE
# =========================================================

def test_filter_towers_by_type():
    response = client.get(
        "/api/v1/towers?tower_type=Micro"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for tower in data:
        assert tower["tower_type"] == "Micro"


# =========================================================
# SEARCH
# =========================================================

def test_search_towers():
    response = client.get(
        "/api/v1/towers?search=Micro"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    assert any(
        tower["tower_name"] == "Micro Tower"
        for tower in data
    )


# =========================================================
# UPDATE
# =========================================================

def test_update_tower():
    response = client.put(
        "/api/v1/towers/1",
        json={
            "tower_name": "Updated Central Tower",
            "coverage_area": 30.0,
            "capacity": 6000,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tower_name"] == "Updated Central Tower"
    assert data["coverage_area"] == 30.0
    assert data["capacity"] == 6000


# =========================================================
# STATUS - MAINTENANCE
# =========================================================

def test_change_tower_status_to_maintenance():
    response = client.patch(
        "/api/v1/towers/1/status",
        json={
            "status": "Maintenance"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Maintenance"


# =========================================================
# STATUS - OFFLINE
# =========================================================

def test_change_tower_status_to_offline():
    response = client.patch(
        "/api/v1/towers/1/status",
        json={
            "status": "Offline"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Offline"


# =========================================================
# STATUS - ACTIVE
# =========================================================

def test_change_tower_status_to_active():
    response = client.patch(
        "/api/v1/towers/1/status",
        json={
            "status": "Active"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Active"


# =========================================================
# STATUS - DECOMMISSIONED
# =========================================================

def test_change_tower_status_to_decommissioned():
    response = client.patch(
        "/api/v1/towers/1/status",
        json={
            "status": "Decommissioned"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Decommissioned"


# =========================================================
# INVALID STATUS
# =========================================================

def test_invalid_tower_status():
    response = client.patch(
        "/api/v1/towers/1/status",
        json={
            "status": "InvalidStatus"
        },
    )

    assert response.status_code == 422


# =========================================================
# INVALID LATITUDE
# =========================================================

def test_invalid_latitude():
    response = create_tower(
        tower_code="TOWER-INVALID-LAT",
        latitude=100,
    )

    assert response.status_code == 422


# =========================================================
# INVALID LONGITUDE
# =========================================================

def test_invalid_longitude():
    response = create_tower(
        tower_code="TOWER-INVALID-LONG",
        longitude=200,
    )

    assert response.status_code == 422


# =========================================================
# INVALID CAPACITY
# =========================================================

def test_invalid_capacity():
    response = create_tower(
        tower_code="TOWER-INVALID-CAPACITY",
        capacity=0,
    )

    assert response.status_code == 422


# =========================================================
# INVALID COVERAGE
# =========================================================

def test_invalid_coverage_area():
    response = create_tower(
        tower_code="TOWER-INVALID-COVERAGE",
        coverage_area=0,
    )

    assert response.status_code == 422


# =========================================================
# DELETE
# =========================================================

def test_delete_tower():
    response = create_tower(
        tower_code="TOWER-DELETE-001",
        tower_name="Delete Tower",
    )

    assert response.status_code == 201

    tower_id = response.json()["id"]

    response = client.delete(
        f"/api/v1/towers/{tower_id}"
    )

    assert response.status_code == 204

    response = client.get(
        f"/api/v1/towers/{tower_id}"
    )

    assert response.status_code == 404
