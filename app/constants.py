"""Application-wide constants."""

API_V1_PREFIX = "/api/v1"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Business thresholds
CENTER_CAPACITY_ALERT_THRESHOLD = 0.85   # alert when >= 85 % of daily capacity is used
MAINTENANCE_DUE_WINDOW_DAYS = 7          # preventive maintenance "due soon" window
PASSWORD_RESET_EXPIRE_MINUTES = 30
MIN_PASSWORD_LENGTH = 8
