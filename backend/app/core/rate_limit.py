"""Shared rate limiter (slowapi) and the limits every route uses.

Routes apply a limit with::

    from app.core.rate_limit import COMPUTE_LIMIT, limiter

    @router.get(...)
    @limiter.limit(COMPUTE_LIMIT)
    def report(request: Request, ...): ...

A route without its own limit gets ``GLOBAL_LIMIT`` from ``enforce_default_limit``,
an app-wide dependency. slowapi's own middleware cannot do it here: it looks
the handler up in ``app.routes``, where FastAPI keeps each included router as
one ``_IncludedRouter`` entry, so every ``/users``, ``/etl`` and ``/analytics``
route would count as exempt. A dependency runs after routing and already
knows the endpoint.
The key is the client IP; behind a trusted proxy, ``ProxyHeadersMiddleware``
has already replaced it with the address from ``X-Forwarded-For``.

Counters live in memory, so they are per process: run a single worker.
"""

import math
import time

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

LOGIN_LIMIT = "5/minute"
REGISTER_LIMIT = "3/minute"
UPLOAD_LIMIT = "10/minute"
# Forecasts (statsmodels) and reports (matplotlib, FPDF2, openpyxl).
COMPUTE_LIMIT = "20/minute"
GLOBAL_LIMIT = "120/minute"

TOO_MANY_REQUESTS = "Demasiadas solicitudes. Intenta de nuevo en un momento."

# "endpoint" keys each counter by route function, so changing a path
# parameter (/reporte-mensual/{mes}) does not open a fresh counter.
limiter = Limiter(key_func=get_remote_address, default_limits=[GLOBAL_LIMIT], key_style="endpoint")


def enforce_default_limit(request: Request) -> None:
    """Apply ``GLOBAL_LIMIT`` to routes without a ``@limiter.limit`` of their own."""
    endpoint = request.scope.get("endpoint")
    if endpoint is None or not limiter.enabled:
        return
    # The slowapi decorator keeps the wrapped name (functools.wraps).
    if f"{endpoint.__module__}.{endpoint.__name__}" in limiter._route_limits:
        return
    limiter._check_request_limit(request, endpoint, in_middleware=True)


def _seconds_until_reset(request: Request, exc: RateLimitExceeded) -> int:
    """Seconds until the exhausted window frees a request, at least 1."""
    current = getattr(request.state, "view_rate_limit", None)
    if current is not None:
        reset_at, _remaining = limiter.limiter.get_window_stats(current[0], *current[1])
        return max(1, math.ceil(reset_at - time.time()))
    if exc.limit is not None:
        return max(1, exc.limit.limit.get_expiry())
    return 60


def rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """429 in Spanish, with ``Retry-After`` so clients know when to retry."""
    return JSONResponse(
        status_code=429,
        content={"detail": TOO_MANY_REQUESTS},
        headers={"Retry-After": str(_seconds_until_reset(request, exc))},
    )
