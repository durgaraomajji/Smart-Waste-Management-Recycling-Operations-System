import enum


class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"
