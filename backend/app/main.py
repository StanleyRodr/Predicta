"""FastAPI application factory for the Predicta API.

Bootstraps:
- CORS middleware (origins from ``CORS_ORIGINS``, see ``app.core.config``)
- Rate limiting on the login endpoint
- Structured logging via loguru
- API routers (users, ETL, analytics)

Schema is managed via Alembic. Run ``alembic upgrade head`` before
starting the server for the first time.
"""

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from starlette.responses import JSONResponse

from app.api import analytics_routes, etl_routes, user_routes
from app.core.config import settings
from app.core.database import engine
from app.core.rate_limit import limiter

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
# Application
# ============================================================
app = FastAPI(
    title="Predicta API",
    description="Motor de analisis y prediccion de ventas para PyMEs",
    version="0.2.0",
    lifespan=lifespan,
)

@app.middleware("http")
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


# CORS: explicit origins; "*" is only accepted in development (see config).
# Registered after the error middleware above, so CORS wraps it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.state.limiter = limiter
# slowapi's handler narrows the exception type, which Starlette's signature rejects.
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


# ============================================================
# Routers
# ============================================================
app.include_router(user_routes.router)
app.include_router(etl_routes.router)
app.include_router(analytics_routes.router)


# ============================================================
# Health & root
# ============================================================
@app.get("/health", tags=["Health"])
def healthcheck() -> dict:
    """Lightweight liveness probe: confirms the API process is up."""
    return {"status": "ok"}


@app.get("/health/db", tags=["Health"], response_model=None)
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


@app.get("/", tags=["Health"])
def root(request: Request) -> dict:
    """Service banner; useful for quick connectivity checks."""
    return {
        "service": "Predicta API",
        "version": app.version,
        "docs": str(request.url_for("swagger_ui")),
    }
