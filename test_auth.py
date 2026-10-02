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
    return f"user_{uuid.uuid4().hex}@example.com"


def register_user(
    role="Customer",
    email=None,
    password="Password@123",
):
    return client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": email or unique_email(),
            "phone": "9876543210",
            "password": password,
            "role": role,
        },
    )


def login_user(
    email,
    password="Password@123",
):
    return client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def test_register_customer():
    response = register_user()

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Test User"
    assert data["role"] == "Customer"
    assert data["is_active"] is True
    assert "password_hash" not in data


def test_duplicate_email():
    email = unique_email()

    first = register_user(
        email=email
    )

    assert first.status_code == 201

    second = register_user(
        email=email
    )

    assert second.status_code == 409


def test_login():
    email = unique_email()

    register = register_user(
        email=email,
        password="Password@123",
    )

    assert register.status_code == 201

    response = login_user(
        email=email,
        password="Password@123",
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_password():
    email = unique_email()

    register_user(
        email=email,
        password="Password@123",
    )

    response = login_user(
        email=email,
        password="WrongPassword@123",
    )

    assert response.status_code == 401


def test_current_user():
    email = unique_email()

    register_user(
        email=email,
        password="Password@123",
    )

    login = login_user(
        email=email,
        password="Password@123",
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == email


def test_refresh_token():
    email = unique_email()

    register_user(
        email=email,
        password="Password@123",
    )

    login = login_user(
        email=email,
        password="Password@123",
    )

    assert login.status_code == 200

    refresh_token = login.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data


def test_old_refresh_token_cannot_be_used_again():
    email = unique_email()

    register_user(
        email=email,
        password="Password@123",
    )

    login = login_user(
        email=email,
        password="Password@123",
    )

    refresh_token = login.json()["refresh_token"]

    first_refresh = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token
        },
    )

    assert first_refresh.status_code == 200

    second_refresh = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token
        },
    )

    assert second_refresh.status_code == 401


def test_invalid_refresh_token():
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "invalid-token"
        },
    )

    assert response.status_code == 401


def test_logout():
    email = unique_email()

    register_user(
        email=email,
        password="Password@123",
    )

    login = login_user(
        email=email,
        password="Password@123",
    )

    assert login.status_code == 200

    refresh_token = login.json()["refresh_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": refresh_token
        },
    )

    assert logout.status_code == 200
    assert logout.json()["message"] == "Logout successful"

    refresh_after_logout = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token
        },
    )

    assert refresh_after_logout.status_code == 401


def test_customer_cannot_deactivate_user():
    customer_email = unique_email()

    register_user(
        role="Customer",
        email=customer_email,
        password="Password@123",
    )

    login = login_user(
        email=customer_email,
        password="Password@123",
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/999/deactivate",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403


def test_customer_cannot_activate_user():
    customer_email = unique_email()

    register_user(
        role="Customer",
        email=customer_email,
        password="Password@123",
    )

    login = login_user(
        email=customer_email,
        password="Password@123",
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/999/activate",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403


def test_super_admin_can_deactivate_user():
    admin_email = unique_email()
    customer_email = unique_email()

    admin = register_user(
        role="Super Admin",
        email=admin_email,
        password="Password@123",
    )

    customer = register_user(
        role="Customer",
        email=customer_email,
        password="Password@123",
    )

    assert admin.status_code == 201
    assert customer.status_code == 201

    admin_id = admin.json()["id"]
    customer_id = customer.json()["id"]

    login = login_user(
        email=admin_email,
        password="Password@123",
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.patch(
        f"/api/v1/auth/{customer_id}/deactivate",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    assert admin_id != customer_id


def test_super_admin_can_activate_user():
    admin_email = unique_email()
    customer_email = unique_email()

    admin = register_user(
        role="Super Admin",
        email=admin_email,
        password="Password@123",
    )

    customer = register_user(
        role="Customer",
        email=customer_email,
        password="Password@123",
    )

    assert admin.status_code == 201
    assert customer.status_code == 201

    customer_id = customer.json()["id"]

    login = login_user(
        email=admin_email,
        password="Password@123",
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    deactivate = client.patch(
        f"/api/v1/auth/{customer_id}/deactivate",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert deactivate.status_code == 200

    activate = client.patch(
        f"/api/v1/auth/{customer_id}/activate",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert activate.status_code == 200
    assert activate.json()["is_active"] is True


def test_deactivated_user_cannot_login():
    admin_email = unique_email()
    customer_email = unique_email()

    register_user(
        role="Super Admin",
        email=admin_email,
        password="Password@123",
    )

    customer = register_user(
        role="Customer",
        email=customer_email,
        password="Password@123",
    )

    customer_id = customer.json()["id"]

    admin_login = login_user(
        email=admin_email,
        password="Password@123",
    )

    admin_token = admin_login.json()["access_token"]

    deactivate = client.patch(
        f"/api/v1/auth/{customer_id}/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert deactivate.status_code == 200

    login = login_user(
        email=customer_email,
        password="Password@123",
    )

    assert login.status_code == 403
    assert login.json()["detail"] == "User account is inactive"


def test_inactive_user_cannot_access_me():
    admin_email = unique_email()
    customer_email = unique_email()

    register_user(
        role="Super Admin",
        email=admin_email,
        password="Password@123",
    )

    register_user(
        role="Customer",
        email=customer_email,
        password="Password@123",
    )

    customer_login = login_user(
        email=customer_email,
        password="Password@123",
    )

    customer_token = customer_login.json()["access_token"]

    admin_login = login_user(
        email=admin_email,
        password="Password@123",
    )

    admin_token = admin_login.json()["access_token"]

    customer_me = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert customer_me.status_code == 200

    customer_id = customer_me.json()["id"]

    deactivate = client.patch(
        f"/api/v1/auth/{customer_id}/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert deactivate.status_code == 200

    me_after_deactivation = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {customer_token}"
        },
    )

    assert me_after_deactivation.status_code == 403
    assert (
        me_after_deactivation.json()["detail"]
        == "User account is inactive"
    )


def test_cannot_deactivate_own_admin_account():
    admin_email = unique_email()

    register = register_user(
        role="Super Admin",
        email=admin_email,
        password="Password@123",
    )

    admin_id = register.json()["id"]

    login = login_user(
        email=admin_email,
        password="Password@123",
    )

    token = login.json()["access_token"]

    response = client.patch(
        f"/api/v1/auth/{admin_id}/deactivate",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "You cannot deactivate your own account"
    )


def test_forgot_password():
    email = unique_email()

    register = register_user(
        email=email,
        password="Password@123",
    )

    assert register.status_code == 201

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": email
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["message"]
        == (
            "If the email exists, "
            "password reset instructions will be sent"
        )
    )

    assert "reset_token" in data
    assert data["reset_token"]


def test_forgot_password_unknown_email():
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": unique_email()
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["message"]
        == (
            "If the email exists, "
            "password reset instructions will be sent"
        )
    )

    assert "reset_token" not in data


def test_reset_password():
    email = unique_email()

    register_user(
        email=email,
        password="Password@123",
    )

    forgot = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": email
        },
    )

    assert forgot.status_code == 200

    reset_token = forgot.json()["reset_token"]

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "NewPassword@123",
        },
    )

    assert reset.status_code == 200
    assert (
        reset.json()["message"]
        == "Password reset successful"
    )

    login = login_user(
        email=email,
        password="NewPassword@123",
    )

    assert login.status_code == 200


def test_old_password_does_not_work_after_reset():
    email = unique_email()

    register_user(
        email=email,
        password="Password@123",
    )

    forgot = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": email
        },
    )

    reset_token = forgot.json()["reset_token"]

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "NewPassword@123",
        },
    )

    assert reset.status_code == 200

    old_password_login = login_user(
        email=email,
        password="Password@123",
    )

    assert old_password_login.status_code == 401


def test_reset_token_can_only_be_used_once():
    email = unique_email()

    register_user(
        email=email,
        password="Password@123",
    )

    forgot = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": email
        },
    )

    reset_token = forgot.json()["reset_token"]

    first_reset = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "NewPassword@123",
        },
    )

    assert first_reset.status_code == 200

    second_reset = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "AnotherPassword@123",
        },
    )

    assert second_reset.status_code == 400


def test_invalid_password_reset_token():
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "invalid-reset-token",
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 400


def test_invalid_access_token():
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401