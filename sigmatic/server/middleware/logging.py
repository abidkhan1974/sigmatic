"""Structured HTTP access logging middleware.

Logs one line per request:
    GET /v1/signals 200 12.4ms req=a1b2c3d4

WebSocket upgrade requests are passed through without logging (they have
no meaningful status code until the connection closes).

Usage
-----
Add to the FastAPI app **before** other middleware so it wraps everything:

    from sigmatic.server.middleware.logging import RequestLoggingMiddleware
    app.add_middleware(RequestLoggingMiddleware)
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("sigmatic.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log method, path, status code, and wall-clock duration for each HTTP request."""

    async def dispatch(self, request: Request, call_next: object) -> Response:
        # Skip WebSocket upgrades — they have no normal response status
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)  # type: ignore[operator]

        request_id = uuid.uuid4().hex[:8]
        start = time.perf_counter()

        try:
            response: Response = await call_next(request)  # type: ignore[operator]
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "%s %s 500 %.1fms req=%s",
                request.method,
                request.url.path,
                duration_ms,
                request_id,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            level,
            "%s %s %d %.1fms req=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response
