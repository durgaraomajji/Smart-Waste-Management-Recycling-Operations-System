import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    OPERATIONS_MANAGER = "operations_manager"
    COLLECTION_SUPERVISOR = "collection_supervisor"
    DRIVER = "driver"
    RECYCLING_CENTER_MANAGER = "recycling_center_manager"
    FIELD_WORKER = "field_worker"
    CUSTOMER = "customer"
