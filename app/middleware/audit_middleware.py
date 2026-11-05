import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("audit")
MUTATING = {"POST", "PUT", "PATCH", "DELETE"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Access log for state-changing requests (method, path, status, latency, request id).

    Business-level audit records (actor / action / entity / change details) are written to the
    `audit_logs` table by the services inside the same database transaction as the change itself.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        if request.method in MUTATING:
            logger.info(
                "%s %s -> %s (%.1f ms) rid=%s",
                request.method,
                request.url.path,
                response.status_code,
                (time.perf_counter() - start) * 1000,
                getattr(request.state, "request_id", "-"),
            )
        return response
