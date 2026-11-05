import enum


class DisposalStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISPOSED = "disposed"


class DisposalMethod(str, enum.Enum):
    LANDFILL = "landfill"
    INCINERATION = "incineration"
    COMPOSTING = "composting"
    HAZARDOUS_TREATMENT = "hazardous_treatment"
    EWASTE_TREATMENT = "ewaste_treatment"
