"""Request-duration histogram for the API (issue #622, R2).

`http_request_duration_seconds{method, route, status_class}` on the manager's metrics registry. The labels are bounded by construction:
`route` is the matched route's TEMPLATE (`/api/v1/entities/{entity_id}`, never the raw path) and a request that matched no route gets the
fixed label `unmatched`; `status_class` is `1xx`..`5xx`; `method` is one of a fixed set, anything else is `OTHER`. HTTP requests only
(websockets are not timed). A pure ASGI middleware, so streaming responses are not buffered.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

from prometheus_client import CollectorRegistry, Histogram

logger = logging.getLogger(__name__)

METRIC_NAME = "http_request_duration_seconds"
UNMATCHED_ROUTE = "unmatched"
_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"})
_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


def status_class(status_code: int) -> str:
    """`2xx` for 200..299 and so on; a code outside 100..599 is `other`."""
    return f"{status_code // 100}xx" if 100 <= status_code <= 599 else "other"


class HttpRequestMetrics:
    """The request-duration histogram, registered on `registry`."""

    def __init__(self, registry: CollectorRegistry) -> None:
        self._histogram = Histogram(METRIC_NAME, "HTTP request duration in seconds, by method, route template and status class",
                                    ["method", "route", "status_class"], buckets=_BUCKETS, registry=registry)

    def observe(self, method: str, route: Optional[str], status_code: int, seconds: float) -> None:
        """Record one request. `route` is the matched route's template, or None when no route matched."""
        self._histogram.labels(method if method in _METHODS else "OTHER", route or UNMATCHED_ROUTE, status_class(status_code)).observe(seconds)


_active: Optional[HttpRequestMetrics] = None


def activate(metrics: HttpRequestMetrics) -> None:
    """Make `metrics` the histogram the middleware records into (the manager does this when it starts)."""
    global _active
    _active = metrics


def deactivate(metrics: HttpRequestMetrics) -> None:
    """Stop recording into `metrics` if it is the active one (the manager does this when it stops)."""
    global _active
    if _active is metrics:
        _active = None


class RequestDurationMiddleware:
    """Times each HTTP request into the active histogram; does nothing while none is active."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        """Run the request, then record its duration, route template and status class."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = time.perf_counter()
        status = {"code": 500}  # an exception before the response starts is a 500

        async def capture(message: Any) -> None:
            if message["type"] == "http.response.start":
                status["code"] = int(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, capture)
        finally:
            self._record(scope, status["code"], time.perf_counter() - started)

    @staticmethod
    def _record(scope: Any, status_code: int, seconds: float) -> None:
        metrics = _active
        if metrics is None:
            return
        try:
            route = getattr(scope.get("route"), "path", None)  # set by the router once a route matched
            metrics.observe(scope.get("method", ""), route, status_code, seconds)
        except Exception:  # metrics never fail a request
            logger.debug("request duration not recorded", exc_info=True)
