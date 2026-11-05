import enum


class CollectionStatus(str, enum.Enum):
    STARTED = "started"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    MISSED = "missed"
