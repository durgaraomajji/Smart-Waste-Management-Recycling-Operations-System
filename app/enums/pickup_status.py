import enum


class PickupStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ASSIGNED = "assigned"
    SCHEDULED = "scheduled"
    COLLECTED = "collected"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# allowed transitions for the pickup workflow
PICKUP_TRANSITIONS = {
    PickupStatus.PENDING: {PickupStatus.APPROVED, PickupStatus.REJECTED, PickupStatus.CANCELLED},
    PickupStatus.APPROVED: {PickupStatus.ASSIGNED, PickupStatus.CANCELLED},
    PickupStatus.ASSIGNED: {PickupStatus.SCHEDULED, PickupStatus.APPROVED, PickupStatus.CANCELLED},
    PickupStatus.SCHEDULED: {PickupStatus.COLLECTED, PickupStatus.APPROVED, PickupStatus.CANCELLED},
    PickupStatus.COLLECTED: set(),
    PickupStatus.CANCELLED: set(),
    PickupStatus.REJECTED: set(),
}
