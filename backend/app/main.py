"""FastAPI application factory for the Predicta API.

Bootstraps:
- Client IP from ``X-Forwarded-For`` only behind ``TRUSTED_PROXIES``
- Security headers, request body size limit, CORS (origins from ``CORS_ORIGINS``)
- Rate limits per IP: per route where declared, ``GLOBAL_LIMIT`` elsewhere
  (an app-wide dependency, see ``app.core.rate_limit``)
- Swagger and ReDoc only outside production
- Structured logging via loguru
- API routers (users, ETL, analytics)

Schema is managed via Alembic. Run ``alembic upgrade head`` before
starting the server for the first time.
"""

import sys
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from starlette.responses import JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.api import analytics_routes, etl_routes, user_routes
from app.core.config import Settings, settings
from app.core.database import engine
from app.core.middleware import BodySizeLimitMiddleware, SecurityHeadersMiddleware
from app.core.rate_limit import enforce_default_limit, limiter, rate_limit_exceeded

# ============================================================
# Logging
# ============================================================
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - "
    "<level>{message}</level>",
)


# ============================================================
# Lifecycle
# ============================================================
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Verify database connectivity on startup; log the result."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection OK")
    except Exception as exc:
        logger.error(f"Database connection failed: {exc}")
        raise
    yield
    logger.info("Shutting down")


# ============================================================
# Handlers shared by every app instance
# ============================================================
async def unhandled_error_as_json(request: Request, call_next):
    """Turn an unhandled exception into a generic 500 inside the CORS layer.

    Starlette answers unhandled errors from its outermost middleware, which
    sits outside ``CORSMiddleware``. That response has no CORS headers, so the
    browser drops it and the frontend reports the API as unreachable. This
    middleware is registered before CORS, which makes it the inner layer.
    """
    try:
        return await call_next(request)
    except Exception:  # noqa: BLE001 - last resort for every error a route did not handle
        logger.exception("Error no controlado en {} {}", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Error interno del servidor."})


async def validation_error_without_input(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Answer 422 without echoing what the client sent.

    Pydantic adds ``input`` (the rejected value, a password included), ``ctx``
    and ``url`` to each error. Only ``loc``, ``msg`` and ``type`` are returned.
    """
    errors = [
        {key: error[key] for key in ("loc", "msg", "type") if key in error} for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(errors)})


def healthcheck() -> dict:
    """Lightweight liveness probe: confirms the API process is up."""
    return {"status": "ok"}


def db_healthcheck() -> dict | JSONResponse:
    """Readiness probe: confirms the database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    except Exception:  # noqa: BLE001 - readiness endpoint must report any DB failure
        logger.exception("La comprobacion de disponibilidad de la base de datos fallo.")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "database": "unreachable",
                "detail": "La base de datos no esta disponible.",
            },
        )


# ============================================================
# Application
# ============================================================
def create_app(config: Settings) -> FastAPI:
    """Build the API for ``config``; production hides Swagger and adds HSTS."""
    docs_enabled = not config.is_production
    application = FastAPI(
        title="Predicta API",
        description="Motor de analisis y prediccion de ventas para PyMEs",
        version="0.2.0",
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        # Routes without their own limit share GLOBAL_LIMIT (see rate_limit).
        dependencies=[Depends(enforce_default_limit)],
    )

    # Each add wraps the previous one, so the last added runs first:
    # proxy headers -> security headers -> CORS -> body limit -> errors -> routes.
    application.middleware("http")(unhandled_error_as_json)
    application.add_middleware(BodySizeLimitMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Retry-After"],
    )
    application.add_middleware(SecurityHeadersMiddleware, production=config.is_production)
    application.add_middleware(ProxyHeadersMiddleware, trusted_hosts=config.trusted_proxies)

    application.add_exception_handler(RequestValidationError, validation_error_without_input)  # type: ignore[arg-type]
    application.state.limiter = limiter
    # The handler narrows the exception type, which Starlette's signature rejects.
    application.add_exception_handler(RateLimitExceeded, rate_limit_exceeded)  # type: ignore[arg-type]

    application.include_router(user_routes.router)
    application.include_router(etl_routes.router)
    application.include_router(analytics_routes.router)

    application.add_api_route("/health", healthcheck, methods=["GET"], tags=["Health"])
    application.add_api_route(
        "/health/db", db_healthcheck, methods=["GET"], tags=["Health"], response_model=None
    )

    @application.get("/", tags=["Health"])
    def root() -> dict:
        """Service banner; useful for quick connectivity checks."""
        banner = {"service": "Predicta API", "version": application.version}
        if docs_enabled:
            banner["docs"] = "/docs"
        return banner

    return application


app = create_app(settings)
