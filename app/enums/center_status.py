import enum


class CenterStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    FULL = "full"
