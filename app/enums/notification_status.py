import enum


class NotificationStatus(str, enum.Enum):
    UNREAD = "unread"
    READ = "read"


class NotificationType(str, enum.Enum):
    NEW_PICKUP_REQUEST = "new_pickup_request"
    COLLECTION_ASSIGNMENT = "collection_assignment"
    MISSED_COLLECTION = "missed_collection"
    VEHICLE_BREAKDOWN = "vehicle_breakdown"
    MAINTENANCE_DUE = "maintenance_due"
    CENTER_CAPACITY_ALERT = "center_capacity_alert"
    CUSTOMER_COMPLAINT = "customer_complaint"
    PENDING_APPROVAL = "pending_approval"
