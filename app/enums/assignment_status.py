import enum


class AssignmentStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REASSIGNED = "reassigned"
    CANCELLED = "cancelled"
