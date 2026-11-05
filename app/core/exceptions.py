class AppException(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str = "Internal server error", details=None):
        super().__init__(message)
        self.message = message
        self.details = details


class BadRequestError(AppException):
    status_code, code = 400, "bad_request"


class UnauthorizedError(AppException):
    status_code, code = 401, "unauthorized"


class ForbiddenError(AppException):
    status_code, code = 403, "forbidden"


class NotFoundError(AppException):
    status_code, code = 404, "not_found"


class ConflictError(AppException):
    status_code, code = 409, "conflict"


class ValidationFailedError(AppException):
    status_code, code = 422, "validation_error"


class BusinessRuleError(AppException):
    """A domain rule was violated (e.g. vehicle capacity exceeded)."""
    status_code, code = 422, "business_rule_violation"
