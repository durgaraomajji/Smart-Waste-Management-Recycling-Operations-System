import enum


class TransferStatus(str, enum.Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
