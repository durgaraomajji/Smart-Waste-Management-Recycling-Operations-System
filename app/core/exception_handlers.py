import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException

logger = logging.getLogger("app")


def _body(code: str, message: str, details=None, request: Request | None = None) -> dict:
    body = {"success": False, "error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    rid = getattr(request.state, "request_id", None) if request else None
    if rid:
        body["request_id"] = rid
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message, exc.details, request))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        errors = [
            {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422, content=_body("validation_error", "Request validation failed", errors, request)
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        codes = {400: "bad_request", 401: "unauthorized", 403: "forbidden", 404: "not_found", 405: "method_not_allowed", 501: "not_implemented"}
        response = JSONResponse(
            status_code=exc.status_code,
            content=_body(codes.get(exc.status_code, "http_error"), str(exc.detail), None, request),
        )
        if exc.headers:
            response.headers.update(exc.headers)  # keeps WWW-Authenticate on 401
        return response

    @app.exception_handler(IntegrityError)
    async def integrity_handler(request: Request, exc: IntegrityError):
        logger.warning("Integrity error: %s", exc.orig)
        return JSONResponse(
            status_code=409, content=_body("conflict", "Duplicate or conflicting record", None, request)
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_handler(request: Request, exc: SQLAlchemyError):
        logger.exception("Database error")
        return JSONResponse(status_code=500, content=_body("database_error", "A database error occurred", None, request))

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error")
        return JSONResponse(status_code=500, content=_body("internal_error", "Internal server error", None, request))
