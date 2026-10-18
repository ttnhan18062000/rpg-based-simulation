"""The backend's internal metrics port (issue #622, R1).

`/metrics` on the API port (8000) is behind the API key, so nothing can scrape it. This serves the same registry (the one
`V2EngineManager.metrics_registry` holds) on a second, unauthenticated port, 9109 by default, the same pattern as the ai_worker's 9108
(`src/observability/stream/lag_metrics.py`). It is meant for the compose network only: the deploy files `expose` it and never `publish` it.
The API app does not mount it and `/metrics` on 8000 is unchanged.

A metrics failure never stops the API: a port that cannot be bound is logged and the API runs without it.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

from prometheus_client import start_http_server

logger = logging.getLogger(__name__)

DEFAULT_METRICS_PORT = 9109
METRICS_PORT_ENV = "BACKEND_METRICS_PORT"


def metrics_port_from_env(environ: Optional[dict] = None) -> int:
    """The port named by BACKEND_METRICS_PORT, else the default; an unusable value falls back to the default."""
    raw = (os.environ if environ is None else environ).get(METRICS_PORT_ENV)
    if raw is None or str(raw).strip() == "":
        return DEFAULT_METRICS_PORT
    try:
        port = int(raw)
    except ValueError:
        logger.warning("%s=%r is not an integer; using %d", METRICS_PORT_ENV, raw, DEFAULT_METRICS_PORT)
        return DEFAULT_METRICS_PORT
    if not 0 <= port <= 65535:
        logger.warning("%s=%r is not a port; using %d", METRICS_PORT_ENV, raw, DEFAULT_METRICS_PORT)
        return DEFAULT_METRICS_PORT
    return port


@dataclass
class MetricsPort:
    """A running metrics server: the port it is bound to (port 0 asks the OS for a free one) and how to stop it."""

    port: int
    _server: Any

    def stop(self) -> None:
        """Stop serving and release the port."""
        self._server.shutdown()
        self._server.server_close()


def start_metrics_port(registry: Any, port: Optional[int] = None) -> Optional[MetricsPort]:
    """Serve `registry` at /metrics on `port` (BACKEND_METRICS_PORT, default 9109) on every interface, without auth.

    Returns the running server, or None when the port cannot be bound (logged, never raised)."""
    wanted = metrics_port_from_env() if port is None else port
    try:
        server, _thread = start_http_server(wanted, addr="0.0.0.0", registry=registry)
    except OSError as exc:
        logger.warning("backend metrics port %d not served: %s", wanted, exc)
        return None
    bound = server.server_port
    logger.info("backend metrics served on port %d", bound)
    return MetricsPort(port=bound, _server=server)
