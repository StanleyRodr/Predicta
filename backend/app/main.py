"""FastAPI application factory for the Predicta API.

Bootstraps:
- CORS middleware (origins from ``CORS_ORIGINS`` env var)
- Rate limiting on the login endpoint
- Structured logging via loguru
- API routers (users, ETL, analytics)

Schema is managed via Alembic. Run ``alembic upgrade head`` before
starting the server for the first time.
"""

import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from starlette.responses import JSONResponse

from app.api import analytics_routes, etl_routes, user_routes
from app.core.database import engine
from app.core.rate_limit import limiter

load_dotenv()

# ============================================================
# Logging
# ============================================================
logger.remove()
logger.add(
    sys.stdout,
    level=os.getenv("LOG_LEVEL", "INFO"),
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

# CORS: comma-separated list in env, "*" only for local dev.
cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
cors_origins: list[str] = (
    ["*"] if cors_origins_raw.strip() == "*" else [o.strip() for o in cors_origins_raw.split(",")]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


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
