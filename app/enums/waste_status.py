import enum


class RecyclabilityStatus(str, enum.Enum):
    RECYCLABLE = "recyclable"
    PARTIALLY_RECYCLABLE = "partially_recyclable"
    NON_RECYCLABLE = "non_recyclable"
    HAZARDOUS = "hazardous"
