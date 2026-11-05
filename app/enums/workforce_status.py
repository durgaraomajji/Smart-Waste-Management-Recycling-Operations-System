import enum


class WorkforceStatus(str, enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    ON_LEAVE = "on_leave"
    INACTIVE = "inactive"
