import enum


class ComplaintStatus(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"


class ComplaintCategory(str, enum.Enum):
    MISSED_PICKUP = "missed_pickup"
    LATE_PICKUP = "late_pickup"
    VEHICLE_ISSUE = "vehicle_issue"
    STAFF_BEHAVIOUR = "staff_behaviour"
    OVERFLOWING_BIN = "overflowing_bin"
    OTHER = "other"
