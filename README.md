# Telecom Service & Network Management System

A production-oriented **FastAPI backend application** for managing telecom customers, service plans, SIM cards, devices, subscriptions, network infrastructure, outages, support tickets, SLA monitoring, technicians, usage analytics, reports, dashboards, notifications, and audit logs.

---

## 🚀 Project Overview

The Telecom Service & Network Management System provides APIs for telecom operations and customer service management.

The system supports multiple user roles and provides secure authentication, role-based authorization, service management, network monitoring, support-ticket management, SLA tracking, reporting, and auditing.

---

## 🛠️ Technology Stack

* **Python:** 3.11+
* **FastAPI**
* **Pydantic**
* **SQLAlchemy**
* **PostgreSQL**
* **JWT Authentication**
* **Alembic**
* **Pytest**
* **Swagger / OpenAPI**
* **Uvicorn**
* **HTTPBearer Authentication**

Optional technologies supported by the architecture:

* Redis
* Celery
* Background Tasks
* Docker

---

## 📁 Project Structure

```text
telecom_service_network/
│
├── core/
│   ├── config.py
│   ├── security.py
│   └── dependencies.py
│
├── db/
│   └── database.py
│
├── models/
│   ├── user.py
│   ├── customer.py
│   ├── plan.py
│   ├── sim.py
│   ├── device.py
│   ├── subscription.py
│   ├── usage.py
│   ├── tower.py
│   ├── network_equipment.py
│   ├── network_outage.py
│   ├── support_ticket.py
│   ├── sla_rule.py
│   ├── ticket_sla.py
│   ├── technician.py
│   ├── technician_assignment.py
│   ├── service_request.py
│   ├── service_request_history.py
│   └── audit_log.py
│
├── repositories/
│   ├── user_repository.py
│   ├── customer_repository.py
│   ├── plan_repository.py
│   ├── sim_repository.py
│   ├── subscription_repository.py
│   ├── usage_repository.py
│   ├── network_outage_repository.py
│   ├── support_ticket_repository.py
│   ├── sla_repository.py
│   ├── technician_repository.py
│   ├── audit_log_repository.py
│   └── ...
│
├── schemas/
│   ├── user.py
│   ├── customer.py
│   ├── plan.py
│   ├── sim.py
│   ├── subscription.py
│   ├── usage.py
│   ├── network_outage.py
│   ├── support_ticket.py
│   ├── sla.py
│   ├── technician.py
│   └── ...
│
├── services/
│   ├── auth_service.py
│   ├── customer_service.py
│   ├── plan_service.py
│   ├── sim_service.py
│   ├── subscription_service.py
│   ├── usage_service.py
│   ├── network_outage_service.py
│   ├── support_ticket_service.py
│   ├── sla_service.py
│   ├── technician_service.py
│   ├── audit_log_service.py
│   └── ...
│
├── routes/
│   ├── auth.py
│   ├── customers.py
│   ├── plans.py
│   ├── sims.py
│   ├── devices.py
│   ├── subscriptions.py
│   ├── usage.py
│   ├── towers.py
│   ├── network_equipment.py
│   ├── network_outages.py
│   ├── support_tickets.py
│   ├── sla.py
│   ├── technicians.py
│   ├── service_requests.py
│   ├── dashboard.py
│   ├── reports.py
│   └── audit_logs.py
│
├── tests/
│   └── integration/
│       ├── test_auth.py
│       ├── test_customer.py
│       ├── test_plans.py
│       ├── test_sim.py
│       ├── test_devices.py
│       ├── test_subscriptions.py
│       ├── test_usage.py
│       ├── test_towers.py
│       ├── test_equipment.py
│       ├── test_outages.py
│       ├── test_support_tickets.py
│       ├── test_sla.py
│       ├── test_technicians.py
│       ├── test_reports.py
│       └── test_audit_logs.py
│
├── alembic/
├── alembic.ini
├── main.py
├── requirements.txt
├── .env
└── README.md
```

---

# 🔐 Authentication & Authorization

The application uses **JWT-based authentication**.

Supported roles:

```text
Super Admin
Operations Manager
Support Agent
Network Engineer
Field Technician
Customer
```

Security features include:

* User registration
* User login
* JWT access tokens
* JWT refresh tokens
* Password hashing
* Password reset
* Logout
* Role-based access control
* Active/inactive account protection
* Protected API endpoints
* HTTP Bearer authentication
* Global exception handling

---

# 👥 Customer Management

The system supports:

* Customer registration
* Customer profile creation
* Customer updates
* Customer activation/deactivation
* KYC status management
* Customer history
* Customer subscription management

KYC statuses:

```text
Pending
Verified
Rejected
```

---

# 📋 Plan Management

Telecom service plans support:

* Prepaid plans
* Postpaid plans
* Data plans
* Voice plans
* SMS plans
* Pricing
* Validity
* Data limits
* Voice limits
* SMS limits
* Plan activation/deactivation

---

# 📱 SIM Management

SIM management supports:

* Physical SIM
* eSIM
* SIM activation
* SIM suspension
* SIM blocking
* SIM replacement
* SIM assignment to customers
* SIM assignment to plans
* SIM-to-tower association
* SIM status tracking

SIM statuses:

```text
Available
Active
Suspended
Lost
Blocked
Deactivated
```

---

# 📲 Device Management

Supported device operations include:

* Device registration
* IMEI tracking
* Manufacturer/model information
* Device type management
* Customer association
* Device status management
* Device/SIM mapping

Supported device types include:

```text
Smartphone
Tablet
Router
Modem
Other
```

---

# 🔄 Subscription Management

Subscriptions connect:

```text
Customer
   ↓
SIM
   ↓
Plan
```

Features include:

* Subscription creation
* Activation
* Suspension
* Cancellation
* Expiration
* Start/end date tracking
* Subscription history

---

# 📊 Usage Management

Usage tracking supports:

* Data usage
* Voice usage
* SMS usage
* Customer-level usage
* SIM-level usage
* Subscription-level usage
* Usage-date filtering
* Usage analytics

Usage types:

```text
Data
Voice
SMS
```

---

# 📡 Network Tower Management

Network towers support:

* Tower registration
* Tower code
* Tower name
* Tower type
* Latitude/longitude
* Coverage area
* Capacity
* Tower status
* SIM/tower association

Tower statuses:

```text
Active
Maintenance
Offline
Decommissioned
```

---

# 🖧 Network Equipment Management

Network equipment management supports:

* Routers
* Switches
* Base stations
* Network devices
* Installation dates
* Maintenance schedules
* CPU usage
* Memory usage
* Network status
* Last heartbeat
* Downtime tracking
* Equipment health monitoring

---

# 🚨 Network Outage Management

The system supports:

* Network outage creation
* Outage severity
* Outage start time
* Expected resolution
* Actual resolution
* Tower association
* Affected customer identification
* Outage resolution

Severity levels:

```text
Low
Medium
High
Critical
```

Affected customers are identified using active SIMs and active subscriptions associated with affected network towers.

---

# 🎫 Support Ticket Management

Support tickets provide:

* Ticket creation
* Ticket categories
* Ticket priorities
* Ticket status tracking
* Agent assignment
* Technician assignment
* Escalation
* Resolution notes
* Ticket resolution
* Ticket closure

Ticket categories include:

```text
Network Issue
SIM Issue
Data Issue
Voice Issue
Device Issue
Account Issue
Service Request
```

Ticket priorities:

```text
Low
Medium
High
Critical
```

---

# ⏱️ SLA Management

The SLA module provides:

* SLA rule creation
* Automatic SLA matching
* Ticket SLA start
* SLA deadline calculation
* SLA status
* Warning status
* SLA breach detection
* SLA resolution
* Escalation tracking
* Soon-to-breach monitoring

Example:

```text
SLA Rule:
Network Issue + High Priority
SLA: 60 minutes
Warning: 30 minutes
```

The system automatically calculates:

```text
Start Time
      +
SLA Minutes
      =
Deadline
```

---

# 👷 Technician Management

Technician functionality includes:

* Technician registration
* Employee ID
* Availability tracking
* Service area
* Location
* Customer/job assignment
* Job status
* Assignment tracking
* Completion tracking

Technician statuses include:

```text
Available
Busy
On Leave
Unavailable
```

---

# 📈 Operations Dashboard

The project includes an operations dashboard for monitoring telecom operations.

Endpoint:

```text
GET /api/v1/dashboard
```

The dashboard provides operational metrics such as customer, subscription, network, ticket, SLA, and other system-level information supported by the implemented dashboard service.

The endpoint requires authentication.

For Swagger:

```text
Authorize → Login as Super Admin → Execute dashboard
```

---

# 📊 Reports

The application provides multiple operational reports.

Available report endpoints:

```text
GET /api/v1/reports/customer-growth

GET /api/v1/reports/subscription-trends

GET /api/v1/reports/plan-popularity

GET /api/v1/reports/data-consumption

GET /api/v1/reports/network-uptime

GET /api/v1/reports/outage-frequency

GET /api/v1/reports/ticket-resolution

GET /api/v1/reports/sla-performance

GET /api/v1/reports/technician-performance

GET /api/v1/reports/customer-service
```

These reports provide operational and analytical information for telecom management.

---

# 📝 Audit Logs

The system records important system activities.

Audit logging covers activities such as:

* Login activity
* Customer updates
* Plan changes
* Subscription changes
* SIM activation
* SIM suspension
* Ticket updates
* Network changes
* Administrative actions

Endpoints:

```text
GET /api/v1/audit-logs

GET /api/v1/audit-logs/{audit_log_id}
```

Each audit log can contain:

```text
User
Action
Entity
Entity ID
Timestamp
Previous Value
New Value
```

---

# 🛡️ Global Error Handling

The project includes global exception handlers for:

* HTTP exceptions
* Request validation errors
* Unexpected server errors

Example validation response:

```json
{
  "detail": "Request validation failed",
  "errors": []
}
```

Unexpected errors return a controlled response rather than exposing internal application details.

---

# 🗄️ Database & Migrations

Database:

```text
PostgreSQL
```

Development database:

```text
telecom_service_network
```

Test database:

```text
telecom_service_network_test
```

PostgreSQL configuration used during development:

```text
localhost:5433
```

Alembic is used for database migrations.

Useful commands:

```powershell
alembic current
```

```powershell
alembic heads
```

```powershell
alembic history
```

```powershell
alembic upgrade head
```

---

# ▶️ Running the Application

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Start the FastAPI server:

```powershell
uvicorn main:app --reload
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

---

# 🧪 Testing

The project uses **Pytest** and FastAPI `TestClient` for integration testing.

Run all tests:

```powershell
python -m pytest -v
```

Run tests quietly:

```powershell
python -m pytest -q
```

Run a specific test module:

```powershell
python -m pytest tests/integration/test_auth.py -v
```

Run with detailed output:

```powershell
python -m pytest tests/integration/test_usage.py -v -s
```

---

# ✅ Successful Test Results

The complete test suite was successfully executed.

```text
422 passed, 1 warning in 394.75s
```

### Test Result

```text
============================= test session starts =============================

422 passed, 1 warning

============================= test session finishes ===========================
```

The warning is related to the Starlette TestClient/httpx compatibility:

```text
StarletteDeprecationWarning:
Using httpx with starlette.testclient is deprecated;
install httpx2 instead.
```

This warning does not cause test failures.

---

# ✅ Major Completed Test Areas

The test suite successfully covers the major backend modules:

```text
Authentication
Customer Management
Plans
SIM Management
Device Management
Subscriptions
Usage Tracking
Network Towers
Network Equipment
Network Outages
Support Tickets
Technicians
SLA Management
Service Requests
Dashboard
Reports
Audit Logs
Security
RBAC
```

---

# 🧪 Important Test Milestones

### Authentication

Verified:

* Registration
* Duplicate email validation
* Login
* Invalid password
* Current user
* Access token
* Refresh token
* Invalid refresh token
* RBAC protection
* Inactive account protection

### Usage

Verified:

* Data usage creation
* Voice usage creation
* SMS usage creation
* Usage retrieval
* Usage listing
* Filtering

### Network Towers

Verified:

* Tower creation
* Tower retrieval
* Tower listing
* Tower status
* Tower information
* Authorization

### Network Equipment

Verified:

* Equipment creation
* Equipment health
* CPU monitoring
* Memory monitoring
* Network status
* Heartbeat
* Maintenance information
* Authorization

### Network Outages

Verified:

* Outage creation
* Tower association
* Affected customer identification
* Outage retrieval
* Outage update
* Outage resolution
* Outage deletion

### Support Tickets

Verified:

* Ticket creation
* Ticket assignment
* Technician assignment
* Status changes
* Ticket resolution
* Ticket tracking

### SLA

Verified:

* SLA rule creation
* Rule matching
* SLA start
* Deadline calculation
* SLA status
* SLA resolution
* SLA monitoring

Example successful SLA calculation:

```text
SLA = 60 minutes

Start:
2026-10-01 12:13:13

Deadline:
2026-10-01 13:13:13
```

### Reports

Verified:

* Customer growth
* Subscription trends
* Plan popularity
* Data consumption
* Network uptime
* Outage frequency
* Ticket resolution
* SLA performance
* Technician performance
* Customer service

### Audit Logs

Verified:

* Audit log creation
* Audit log retrieval
* User association
* Entity tracking
* Action tracking
* Previous/new values
* Protected audit endpoints

Audit tests:

```text
10 passed, 1 warning
```

---

# 🔐 Swagger Authentication

For protected endpoints:

1. Open Swagger:

```text
http://127.0.0.1:8000/docs
```

2. Execute:

```text
POST /api/v1/auth/login
```

3. Login using the Super Admin account.

4. Copy the returned:

```text
access_token
```

5. Click:

```text
Authorize 🔒
```

6. Enter the bearer token.

7. Execute protected endpoints.

For the operations dashboard, reports, and audit logs, the demo flow uses the **Super Admin** account.

---

# 🎯 Mandatory Demo Flow

The completed demonstration workflow is:

```text
Admin Login
      ↓
Create Customer
      ↓
Create Plan
      ↓
Register SIM
      ↓
Register Device
      ↓
Activate Subscription
      ↓
Generate Usage
      ↓
Register Network Tower
      ↓
Create Network Outage
      ↓
Identify Affected Customers
      ↓
Create Support Ticket
      ↓
Assign Agent / Technician
      ↓
Track SLA
      ↓
Resolve Ticket
      ↓
Restore Network
      ↓
Generate Notifications
      ↓
View Operations Dashboard
      ↓
Generate Reports
      ↓
Verify Audit Logs
```

---

# ⭐ Bonus Features

The project also includes the following production-oriented features:

* JWT authentication
* Refresh tokens
* Password hashing
* RBAC
* Inactive account protection
* Global exception handling
* PostgreSQL database
* Alembic migrations
* Usage analytics
* SLA management
* SLA escalation
* Network outage management
* Automatic affected-customer identification
* Technician assignment
* SIM/tower association
* Operations dashboard
* Operational reports
* Audit logging
* Swagger/OpenAPI documentation
* Integration testing
* Service/repository architecture

---

# 🏗️ Architecture

The application follows a layered architecture:

```text
Routes
   ↓
Services
   ↓
Repositories
   ↓
Models
   ↓
PostgreSQL
```

### Routes

Handle HTTP requests and responses.

### Schemas

Validate incoming requests and structure API responses.

### Services

Contain business logic.

### Repositories

Handle database operations.

### Models

Represent database tables.

This separation keeps the application maintainable and scalable.

---

# 👤 Supported User Roles

| Role               | Responsibility                 |
| ------------------ | ------------------------------ |
| Super Admin        | Full system administration     |
| Operations Manager | Telecom operations management  |
| Support Agent      | Customer support and tickets   |
| Network Engineer   | Network infrastructure         |
| Field Technician   | Field service operations       |
| Customer           | Customer services and requests |

---

# 📌 API Documentation

After starting the server, open:

```text
http://127.0.0.1:8000/docs
```

Swagger provides interactive documentation for all available API endpoints.

---

# 🏁 Project Status

## ✅ Project Completed

The Telecom Service & Network Management System includes:

```text
✅ Authentication
✅ Authorization
✅ Customer Management
✅ Plan Management
✅ SIM Management
✅ Device Management
✅ Subscription Management
✅ Usage Tracking
✅ Network Towers
✅ Network Equipment
✅ Network Outages
✅ Support Tickets
✅ Technician Management
✅ SLA Management
✅ Service Requests
✅ Operations Dashboard
✅ Reports
✅ Audit Logs
✅ Global Exception Handling
✅ PostgreSQL
✅ Alembic
✅ Swagger
✅ Pytest Integration Tests
```

### Final Test Status

```text
422 PASSED
1 WARNING
0 FAILED
```

The application is successfully tested and ready for demonstration.
Author

SRIKANTH B
