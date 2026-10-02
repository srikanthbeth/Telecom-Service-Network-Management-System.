from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "Super Admin"
    OPERATIONS_MANAGER = "Operations Manager"
    SUPPORT_AGENT = "Support Agent"
    NETWORK_ENGINEER = "Network Engineer"
    FIELD_TECHNICIAN = "Field Technician"
    CUSTOMER = "Customer"


class AccountStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class KYCStatus(str, Enum):
    PENDING = "Pending"
    VERIFIED = "Verified"
    REJECTED = "Rejected"


class PlanType(str, Enum):
    PREPAID = "Prepaid"
    POSTPAID = "Postpaid"
    DATA = "Data"
    VOICE = "Voice"
    SMS = "SMS"


class PlanStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class SIMType(str, Enum):
    PHYSICAL = "Physical"
    ESIM = "eSIM"


class SIMStatus(str, Enum):
    AVAILABLE = "Available"
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    LOST = "Lost"
    BLOCKED = "Blocked"
    DEACTIVATED = "Deactivated"


class DeviceType(str, Enum):
    SMARTPHONE = "Smartphone"
    TABLET = "Tablet"
    ROUTER = "Router"
    MODEM = "Modem"
    OTHER = "Other"


class DeviceStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    BLOCKED = "Blocked"
    LOST = "Lost"


class SubscriptionStatus(str, Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    CANCELLED = "Cancelled"
    EXPIRED = "Expired"


class UsageType(str, Enum):
    DATA = "Data"
    VOICE = "Voice"
    SMS = "SMS"


class TowerStatus(str, Enum):
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    OFFLINE = "Offline"
    DECOMMISSIONED = "Decommissioned"


class OutageSeverity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TicketStatus(str, Enum):
    OPEN = "Open"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    WAITING_FOR_CUSTOMER = "Waiting for Customer"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class TicketPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TicketCategory(str, Enum):
    NETWORK_ISSUE = "Network Issue"
    SIM_ISSUE = "SIM Issue"
    DATA_ISSUE = "Data Issue"
    VOICE_ISSUE = "Voice Issue"
    DEVICE_ISSUE = "Device Issue"
    ACCOUNT_ISSUE = "Account Issue"
    SERVICE_REQUEST = "Service Request"


class TicketHistoryAction(str, Enum):
    CREATED = "Created"
    ASSIGNED = "Assigned"
    REASSIGNED = "Reassigned"
    PRIORITY_CHANGED = "Priority Changed"
    STATUS_CHANGED = "Status Changed"
    ESCALATED = "Escalated"
    COMMENT_ADDED = "Comment Added"
    RESOLUTION_ADDED = "Resolution Added"
    CLOSED = "Closed"


class ServiceRequestStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"


class NotificationType(str, Enum):
    TICKET_ASSIGNMENT = "Ticket Assignment"
    SLA_BREACH = "SLA Breach"
    NETWORK_OUTAGE = "Network Outage"
    SERVICE_RESTORATION = "Service Restoration"
    PLAN_EXPIRY = "Plan Expiry"
    USAGE_THRESHOLD = "Usage Threshold"
    SIM_SUSPENSION = "SIM Suspension"
    MAINTENANCE = "Maintenance"




class EquipmentType(str, Enum):

    ROUTER = "Router"

    SWITCH = "Switch"

    BASE_STATION = "Base Station"

    NETWORK_DEVICE = "Network Device"


class NetworkStatus(str, Enum):

    ONLINE = "Online"

    OFFLINE = "Offline"

    DEGRADED = "Degraded"

    MAINTENANCE = "Maintenance"


class EquipmentHealth(str, Enum):

    HEALTHY = "Healthy"

    WARNING = "Warning"

    CRITICAL = "Critical"

class TechnicianAvailability(str, Enum):
    AVAILABLE = "Available"
    BUSY = "Busy"
    ON_LEAVE = "On Leave"
    UNAVAILABLE = "Unavailable"


class TechnicianJobStatus(str, Enum):
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class SLAStatus(str, Enum):
    ACTIVE = "Active"
    BREACHED = "Breached"
    RESOLVED = "Resolved"
    CANCELLED = "Cancelled"


class SLAEscalationStatus(str, Enum):
    NOT_ESCALATED = "Not Escalated"
    WARNING = "Warning"
    ESCALATED = "Escalated"

from enum import Enum


class ServiceRequestType(str, Enum):
    SIM_REPLACEMENT = "SIM_REPLACEMENT"
    NUMBER_CHANGE = "NUMBER_CHANGE"
    PLAN_CHANGE = "PLAN_CHANGE"
    DEVICE_REPLACEMENT = "DEVICE_REPLACEMENT"
    SERVICE_ACTIVATION = "SERVICE_ACTIVATION"
    SERVICE_SUSPENSION = "SERVICE_SUSPENSION"
    SERVICE_TERMINATION = "SERVICE_TERMINATION"


class ServiceRequestStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"