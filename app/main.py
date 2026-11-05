import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.router import api_router
from app.constants import API_V1_PREFIX
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.middleware.audit_middleware import AuditMiddleware
from app.middleware.request_id import RequestIDMiddleware

setup_logging()
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.SECRET_KEY.startswith("change-me") and settings.ENVIRONMENT == "production":
        raise RuntimeError("SECRET_KEY must be set to a strong random value in production")
    logger.info("Starting %s (%s)", settings.APP_NAME, settings.ENVIRONMENT)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Waste collection, recycling and disposal operations backend.",
        lifespan=lifespan,
    )
    # Order matters: the last added runs first. Session is needed only for the Google OAuth2 handshake.
    app.add_middleware(AuditMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET, same_site="lax", https_only=settings.ENVIRONMENT == "production")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials="*" not in settings.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix=API_V1_PREFIX)

    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()
