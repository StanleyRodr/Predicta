"""Shared rate-limiter instance for slowapi.

Routes apply limits with::

    from app.core.rate_limit import limiter

    @router.post(...)
    @limiter.limit("5/minute")
    def login(request: Request, ...): ...

The same instance is attached to ``app.state.limiter`` during startup
so slowapi can enforce the limits at request time.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
