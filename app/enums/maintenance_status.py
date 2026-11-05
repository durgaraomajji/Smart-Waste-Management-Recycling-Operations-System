import enum


class MaintenanceStatus(str, enum.Enum):
    REQUESTED = "requested"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    BREAKDOWN = "breakdown"
