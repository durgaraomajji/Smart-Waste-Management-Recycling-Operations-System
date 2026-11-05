import enum


class VehicleStatus(str, enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    IN_SERVICE = "in_service"
    UNDER_MAINTENANCE = "under_maintenance"
    BROKEN_DOWN = "broken_down"
    RETIRED = "retired"


class VehicleType(str, enum.Enum):
    COMPACTOR = "compactor"
    TIPPER = "tipper"
    MINI_TRUCK = "mini_truck"
    OPEN_TRUCK = "open_truck"
    HAZMAT = "hazmat"


class FuelType(str, enum.Enum):
    DIESEL = "diesel"
    PETROL = "petrol"
    CNG = "cng"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
