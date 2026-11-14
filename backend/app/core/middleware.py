"""Pure ASGI middlewares: security headers and request body size limit."""

import json
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

MEGABYTE = 1024 * 1024
# Uploads allow 25 MB of file (etl_service.MAX_UPLOAD_BYTES) plus multipart overhead.
UPLOAD_BODY_LIMIT = 26 * MEGABYTE
DEFAULT_BODY_LIMIT = 1 * MEGABYTE
UPLOAD_PREFIX = "/etl/"
BODY_TOO_LARGE = "La solicitud es demasiado grande."

# Routes that answer with a user's data; browsers and proxies must not keep them.
PRIVATE_PREFIXES = ("/users", "/etl", "/analytics")
# Swagger UI and ReDoc load scripts from a CDN, so they skip the strict CSP.
DOCS_PATHS = ("/docs", "/redoc")
API_CSP = "default-src 'none'; frame-ancestors 'none'"
HSTS = "max-age=31536000; includeSubDomains"


def _path_matches(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in prefixes)


class SecurityHeadersMiddleware:
    """Add the security headers to every HTTP response of the API."""

    def __init__(self, app: ASGIApp, *, production: bool) -> None:
        self.app = app
        self.production = production

    def _headers_for(self, path: str) -> list[tuple[bytes, bytes]]:
        headers = [
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"referrer-policy", b"no-referrer"),
        ]
        if self.production or not _path_matches(path, DOCS_PATHS):
            headers.append((b"content-security-policy", API_CSP.encode()))
        if self.production:
            headers.append((b"strict-transport-security", HSTS.encode()))
        if _path_matches(path, PRIVATE_PREFIXES):
            headers.append((b"cache-control", b"no-store"))
        return headers

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        extra = self._headers_for(scope["path"])

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                present = {name.lower() for name, _ in headers}
                headers.extend(header for header in extra if header[0] not in present)
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


class _BodyTooLargeError(Exception):
    """Raised from ``receive`` once the body passes the limit."""


class BodySizeLimitMiddleware:
    """Answer 413 before the application reads an oversized body.

    ``Content-Length`` is checked first. Without it (chunked), received bytes
    are counted and the read is cut as soon as they pass the limit; the
    application's own response to the broken read is replaced by the 413.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    @staticmethod
    def _limit_for(path: str) -> int:
        return UPLOAD_BODY_LIMIT if path.startswith(UPLOAD_PREFIX) else DEFAULT_BODY_LIMIT

    @staticmethod
    async def _reject(send: Send) -> None:
        body = json.dumps({"detail": BODY_TOO_LARGE}, ensure_ascii=False).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                    (b"connection", b"close"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        limit = self._limit_for(scope["path"])
        for name, value in scope["headers"]:
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    declared = 0
                if declared > limit:
                    await self._reject(send)
                    return

        received = 0
        exceeded = False
        started = False

        async def limited_receive() -> Message:
            nonlocal received, exceeded
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    exceeded = True
                    raise _BodyTooLargeError
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal started
            if exceeded:
                return
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except Exception:
            if not exceeded:
                raise
        if exceeded and not started:
            await self._reject(send)
