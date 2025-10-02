"""Metrics middleware for API."""

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.metrics import api_request_duration


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect API request metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        # Record metrics
        api_request_duration.labels(
            method=request.method, endpoint=request.url.path, status=response.status_code
        ).observe(duration)

        return response
