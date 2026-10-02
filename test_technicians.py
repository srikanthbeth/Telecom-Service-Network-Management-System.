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


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def unique_email(prefix="user"):
    return f"{prefix}_{uuid4().hex[:10]}@example.com"


def register_user(role="Customer", email=None):
    email = email or unique_email(role.lower().replace(" ", "_"))

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Test {role}",
            "email": email,
            "phone": f"9{uuid4().int % 10_000_000_000:010d}",
            "password": "Test@12345",
            "role": role,
        },
    )

    assert response.status_code in [200, 201], response.text

    return {
        "email": email,
        "password": "Test@12345",
        "response": response,
    }


def login_user(email, password="Test@12345"):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data.get("access_token") is not None

    return data["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_admin():
    user = register_user("Super Admin")

    token = login_user(
        user["email"],
        user["password"],
    )

    return token


def get_user_id(response):
    data = response.json()

    if "id" in data:
        return data["id"]

    if "user" in data and isinstance(data["user"], dict):
        return data["user"]["id"]

    raise AssertionError(
        f"User ID not found in response: {data}"
    )


def create_technician_user():
    user = register_user("Field Technician")

    user_id = get_user_id(
        user["response"]
    )

    return user_id


def create_technician(
    admin_token,
    user_id,
    employee_id=None,
):
    employee_id = (
        employee_id
        or f"TECH-{uuid4().hex[:8].upper()}"
    )

    response = client.post(
        "/api/v1/technicians/",
        headers=auth_headers(admin_token),
        json={
            "user_id": user_id,
            "employee_id": employee_id,
            "full_name": "Field Technician",
            "phone": "9876543210",
            "availability": "Available",
            "latitude": 13.6288,
            "longitude": 79.4192,
            "service_area": "Tirupati",
            "address": "Main Service Area",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_assignment(
    admin_token,
    technician_id,
    job_type="Network Installation",
):
    response = client.post(
        "/api/v1/technicians/assignments",
        headers=auth_headers(admin_token),
        json={
            "technician_id": technician_id,
            "job_type": job_type,
            "description": "Test technician job",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def test_register_technician():
    admin_token = create_admin()

    user_id = create_technician_user()

    response = client.post(
        "/api/v1/technicians/",
        headers=auth_headers(admin_token),
        json={
            "user_id": user_id,
            "employee_id": f"TECH-{uuid4().hex[:8].upper()}",
            "full_name": "John Technician",
            "phone": "9876543210",
            "availability": "Available",
            "latitude": 13.6288,
            "longitude": 79.4192,
            "service_area": "Tirupati",
            "address": "Tirupati Service Center",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == user_id
    assert data["full_name"] == "John Technician"
    assert data["availability"] == "Available"
    assert data["service_area"] == "Tirupati"


def test_duplicate_employee_id_fails():
    admin_token = create_admin()

    user1_id = create_technician_user()

    employee_id = f"TECH-{uuid4().hex[:8].upper()}"

    first = client.post(
        "/api/v1/technicians/",
        headers=auth_headers(admin_token),
        json={
            "user_id": user1_id,
            "employee_id": employee_id,
            "full_name": "Technician One",
            "phone": "9876543210",
            "availability": "Available",
        },
    )

    assert first.status_code == 201

    user2_id = create_technician_user()

    second = client.post(
        "/api/v1/technicians/",
        headers=auth_headers(admin_token),
        json={
            "user_id": user2_id,
            "employee_id": employee_id,
            "full_name": "Technician Two",
            "phone": "9876543211",
            "availability": "Available",
        },
    )

    assert second.status_code == 409


def test_same_user_cannot_be_registered_twice():
    admin_token = create_admin()

    user_id = create_technician_user()

    first = client.post(
        "/api/v1/technicians/",
        headers=auth_headers(admin_token),
        json={
            "user_id": user_id,
            "employee_id": f"TECH-{uuid4().hex[:8].upper()}",
            "full_name": "Duplicate Technician",
            "phone": "9876543210",
            "availability": "Available",
        },
    )

    assert first.status_code == 201

    second = client.post(
        "/api/v1/technicians/",
        headers=auth_headers(admin_token),
        json={
            "user_id": user_id,
            "employee_id": f"TECH-{uuid4().hex[:8].upper()}",
            "full_name": "Duplicate Technician",
            "phone": "9876543210",
            "availability": "Available",
        },
    )

    assert second.status_code == 409


def test_get_all_technicians():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    response = client.get(
        "/api/v1/technicians/",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    assert any(
        item["id"] == technician["id"]
        for item in data
    )


def test_get_technician_by_id():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    response = client.get(
        f"/api/v1/technicians/{technician['id']}",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == technician["id"]
    assert data["employee_id"] == technician["employee_id"]


def test_get_nonexistent_technician():
    admin_token = create_admin()

    response = client.get(
        "/api/v1/technicians/999999",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404


def test_update_technician_availability():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    response = client.put(
        f"/api/v1/technicians/{technician['id']}",
        headers=auth_headers(admin_token),
        json={
            "availability": "Busy",
        },
    )

    assert response.status_code == 200

    assert response.json()["availability"] == "Busy"


def test_update_technician_on_leave():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    response = client.put(
        f"/api/v1/technicians/{technician['id']}",
        headers=auth_headers(admin_token),
        json={
            "availability": "On Leave",
        },
    )

    assert response.status_code == 200

    assert response.json()["availability"] == "On Leave"


def test_update_technician_location():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    response = client.put(
        f"/api/v1/technicians/{technician['id']}",
        headers=auth_headers(admin_token),
        json={
            "latitude": 13.6500,
            "longitude": 79.4100,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["latitude"] == 13.6500
    assert data["longitude"] == 79.4100


def test_update_service_area():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    response = client.put(
        f"/api/v1/technicians/{technician['id']}",
        headers=auth_headers(admin_token),
        json={
            "service_area": "Tirupati and Renigunta",
        },
    )

    assert response.status_code == 200

    assert response.json()["service_area"] == (
        "Tirupati and Renigunta"
    )


def test_add_technician_skill():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    response = client.post(
        f"/api/v1/technicians/{technician['id']}/skills",
        headers=auth_headers(admin_token),
        json={
            "skill_name": "Network Installation",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["technician_id"] == technician["id"]
    assert data["skill_name"] == "Network Installation"


def test_add_multiple_skills():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    skills = [
        "Network Installation",
        "Fiber Repair",
        "Router Configuration",
    ]

    for skill in skills:
        response = client.post(
            f"/api/v1/technicians/{technician['id']}/skills",
            headers=auth_headers(admin_token),
            json={
                "skill_name": skill,
            },
        )

        assert response.status_code == 201

    response = client.get(
        f"/api/v1/technicians/{technician['id']}/skills",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    skill_names = [
        item["skill_name"]
        for item in data
    ]

    for skill in skills:
        assert skill in skill_names


def test_duplicate_skill_fails():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    payload = {
        "skill_name": "Fiber Repair",
    }

    first = client.post(
        f"/api/v1/technicians/{technician['id']}/skills",
        headers=auth_headers(admin_token),
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        f"/api/v1/technicians/{technician['id']}/skills",
        headers=auth_headers(admin_token),
        json=payload,
    )

    assert second.status_code == 409


def test_get_skills_for_nonexistent_technician():
    admin_token = create_admin()

    response = client.get(
        "/api/v1/technicians/999999/skills",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404


def test_assign_technician():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    response = create_assignment(
        admin_token,
        technician["id"],
        "Network Installation",
    )

    assert response["technician_id"] == technician["id"]
    assert response["job_type"] == "Network Installation"
    assert response["status"] == "Assigned"


def test_assignment_makes_technician_busy():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    create_assignment(
        admin_token,
        technician["id"],
    )

    response = client.get(
        f"/api/v1/technicians/{technician['id']}",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["availability"] == "Busy"


def test_cannot_assign_unavailable_technician():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    update = client.put(
        f"/api/v1/technicians/{technician['id']}",
        headers=auth_headers(admin_token),
        json={
            "availability": "Unavailable",
        },
    )

    assert update.status_code == 200

    response = client.post(
        "/api/v1/technicians/assignments",
        headers=auth_headers(admin_token),
        json={
            "technician_id": technician["id"],
            "job_type": "Repair",
        },
    )

    assert response.status_code == 400


def test_cannot_assign_technician_on_leave():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    update = client.put(
        f"/api/v1/technicians/{technician['id']}",
        headers=auth_headers(admin_token),
        json={
            "availability": "On Leave",
        },
    )

    assert update.status_code == 200

    response = client.post(
        "/api/v1/technicians/assignments",
        headers=auth_headers(admin_token),
        json={
            "technician_id": technician["id"],
            "job_type": "Repair",
        },
    )

    assert response.status_code == 400


def test_reassign_technician():
    admin_token = create_admin()

    user1_id = create_technician_user()

    technician1 = create_technician(
        admin_token,
        user1_id,
    )

    user2_id = create_technician_user()

    technician2 = create_technician(
        admin_token,
        user2_id,
    )

    assignment = create_assignment(
        admin_token,
        technician1["id"],
    )

    response = client.patch(
        f"/api/v1/technicians/assignments/{assignment['id']}/reassign",
        headers=auth_headers(admin_token),
        json={
            "technician_id": technician2["id"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["technician_id"] == technician2["id"]
    assert data["status"] == "Assigned"


def test_reassign_nonexistent_assignment():
    admin_token = create_admin()

    user_id = create_technician_user()

    create_technician(
        admin_token,
        user_id,
    )

    response = client.patch(
        "/api/v1/technicians/assignments/999999/reassign",
        headers=auth_headers(admin_token),
        json={
            "technician_id": 1,
        },
    )

    assert response.status_code == 404


def test_assignment_status_in_progress():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    assignment = create_assignment(
        admin_token,
        technician["id"],
    )

    response = client.patch(
        f"/api/v1/technicians/assignments/{assignment['id']}/status",
        headers=auth_headers(admin_token),
        json={
            "status": "In Progress",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "In Progress"
    assert data["started_at"] is not None


def test_completed_job():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    assignment = create_assignment(
        admin_token,
        technician["id"],
    )

    response = client.patch(
        f"/api/v1/technicians/assignments/{assignment['id']}/status",
        headers=auth_headers(admin_token),
        json={
            "status": "Completed",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Completed"
    assert data["completed_at"] is not None


def test_completed_job_makes_technician_available():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    assignment = create_assignment(
        admin_token,
        technician["id"],
    )

    response = client.patch(
        f"/api/v1/technicians/assignments/{assignment['id']}/status",
        headers=auth_headers(admin_token),
        json={
            "status": "Completed",
        },
    )

    assert response.status_code == 200

    technician_response = client.get(
        f"/api/v1/technicians/{technician['id']}",
        headers=auth_headers(admin_token),
    )

    assert technician_response.status_code == 200

    assert (
        technician_response.json()["availability"]
        == "Available"
    )


def test_technician_workload():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    for job_type in [
        "Installation",
        "Repair",
        "Maintenance",
    ]:
        response = client.post(
            "/api/v1/technicians/assignments",
            headers=auth_headers(admin_token),
            json={
                "technician_id": technician["id"],
                "job_type": job_type,
            },
        )

        assert response.status_code == 201

    response = client.get(
        f"/api/v1/technicians/{technician['id']}/workload",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["technician_id"] == technician["id"]
    assert data["pending_jobs"] == 3
    assert data["total_workload"] == 3
    assert data["completed_jobs"] == 0


def test_workload_after_completed_job():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    assignment = create_assignment(
        admin_token,
        technician["id"],
    )

    complete = client.patch(
        f"/api/v1/technicians/assignments/{assignment['id']}/status",
        headers=auth_headers(admin_token),
        json={
            "status": "Completed",
        },
    )

    assert complete.status_code == 200

    response = client.get(
        f"/api/v1/technicians/{technician['id']}/workload",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["pending_jobs"] == 0
    assert data["completed_jobs"] == 1
    assert data["total_workload"] == 0


def test_pending_jobs():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    create_assignment(
        admin_token,
        technician["id"],
        "Installation",
    )

    create_assignment(
        admin_token,
        technician["id"],
        "Repair",
    )

    response = client.get(
        f"/api/v1/technicians/{technician['id']}/pending-jobs",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    for job in data:
        assert job["status"] in [
            "Assigned",
            "In Progress",
        ]


def test_completed_jobs():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    assignment = create_assignment(
        admin_token,
        technician["id"],
        "Equipment Repair",
    )

    complete = client.patch(
        f"/api/v1/technicians/assignments/{assignment['id']}/status",
        headers=auth_headers(admin_token),
        json={
            "status": "Completed",
        },
    )

    assert complete.status_code == 200

    response = client.get(
        f"/api/v1/technicians/{technician['id']}/completed-jobs",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == assignment["id"]
    assert data[0]["status"] == "Completed"


def test_pending_and_completed_jobs_are_separated():
    admin_token = create_admin()

    user_id = create_technician_user()

    technician = create_technician(
        admin_token,
        user_id,
    )

    first = create_assignment(
        admin_token,
        technician["id"],
        "Installation",
    )

    second = create_assignment(
        admin_token,
        technician["id"],
        "Repair",
    )

    complete = client.patch(
        f"/api/v1/technicians/assignments/{first['id']}/status",
        headers=auth_headers(admin_token),
        json={
            "status": "Completed",
        },
    )

    assert complete.status_code == 200

    pending = client.get(
        f"/api/v1/technicians/{technician['id']}/pending-jobs",
        headers=auth_headers(admin_token),
    )

    assert pending.status_code == 200

    pending_data = pending.json()

    assert len(pending_data) == 1
    assert pending_data[0]["id"] == second["id"]
    assert pending_data[0]["job_type"] == "Repair"

    completed = client.get(
        f"/api/v1/technicians/{technician['id']}/completed-jobs",
        headers=auth_headers(admin_token),
    )

    assert completed.status_code == 200

    completed_data = completed.json()

    assert len(completed_data) == 1
    assert completed_data[0]["id"] == first["id"]
    assert completed_data[0]["job_type"] == "Installation"


def test_technician_registration_requires_authentication():
    user_id = create_technician_user()

    response = client.post(
        "/api/v1/technicians/",
        json={
            "user_id": user_id,
            "employee_id": f"TECH-{uuid4().hex[:8].upper()}",
            "full_name": "Unauthorized Technician",
            "phone": "9876543210",
            "availability": "Available",
        },
    )

    assert response.status_code == 401


def test_assignment_requires_authentication():
    response = client.post(
        "/api/v1/technicians/assignments",
        json={
            "technician_id": 1,
            "job_type": "Repair",
        },
    )

    assert response.status_code == 401