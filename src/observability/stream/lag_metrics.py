"""Prometheus gauges for the Redis Streams consumer groups the ai_worker reads.

Read-only and out of the tick loop: it asks Redis (XINFO GROUPS) at scrape time and never imports the engine.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, Iterator, Optional

import redis
from prometheus_client import CollectorRegistry, start_http_server
from prometheus_client.core import GaugeMetricFamily

logger = logging.getLogger(__name__)

DEFAULT_METRICS_PORT = 9108
METRICS_PORT_ENV = "AI_WORKER_METRICS_PORT"


def metrics_port_from_env(environ: Optional[dict] = None) -> int:
    """The port named by AI_WORKER_METRICS_PORT, else the default; an unusable value falls back to the default."""
    raw = (os.environ if environ is None else environ).get(METRICS_PORT_ENV)
    if raw is None or str(raw).strip() == "":
        return DEFAULT_METRICS_PORT
    try:
        port = int(raw)
    except ValueError:
        logger.warning("%s=%r is not an integer; using %d", METRICS_PORT_ENV, raw, DEFAULT_METRICS_PORT)
        return DEFAULT_METRICS_PORT
    if not 0 < port < 65536:
        logger.warning("%s=%d is out of range; using %d", METRICS_PORT_ENV, port, DEFAULT_METRICS_PORT)
        return DEFAULT_METRICS_PORT
    return port


class StreamLagCollector:
    """Yields consumer-group lag and pending count per (stream, group), read from Redis at scrape time.

    `client_factory` returns a connected redis client. When Redis cannot be read the scrape yields
    `sim_stream_consumer_up 0` and no gauges, so an alert never sees a stale value.
    """

    def __init__(self, client_factory: Callable[[], Any], stream_names: list[str]) -> None:
        self._client_factory = client_factory
        self._stream_names = list(stream_names)
        self._client: Optional[Any] = None

    def _read(self) -> list[tuple[str, str, Optional[int], int]]:
        if self._client is None:
            self._client = self._client_factory()
        rows: list[tuple[str, str, Optional[int], int]] = []
        for stream in self._stream_names:
            for group in self._client.xinfo_groups(stream):
                lag = group.get("lag")
                rows.append((stream, str(group["name"]), None if lag is None else int(lag), int(group["pending"])))
        return rows

    def collect(self) -> Iterator[Any]:
        """Yield the up gauge, then lag and pending per (stream, group) when Redis answered."""
        up = GaugeMetricFamily("sim_stream_consumer_up", "1 when Redis answered the consumer-group query this scrape, else 0")
        try:
            rows = self._read()
        except (redis.exceptions.RedisError, OSError) as exc:
            logger.error("stream lag read failed: %s", exc)
            self._client = None
            up.add_metric([], 0)
            yield up
            return
        up.add_metric([], 1)
        yield up
        lag_family = GaugeMetricFamily(
            "sim_stream_consumer_lag", "Entries in the stream the consumer group has not yet been delivered", labels=["stream", "group"]
        )
        pending_family = GaugeMetricFamily(
            "sim_stream_pending_messages", "Entries delivered to the consumer group and not yet acknowledged", labels=["stream", "group"]
        )
        for stream, group, lag, pending in rows:
            if lag is not None:  # Redis reports no lag when it cannot compute one; a missing sample beats a wrong one
                lag_family.add_metric([stream, group], lag)
            pending_family.add_metric([stream, group], pending)
        yield lag_family
        yield pending_family


def redis_client_factory(redis_url: str) -> Callable[[], Any]:
    """A factory for a decoded-response Redis client with short socket timeouts."""

    def make() -> Any:
        return redis.from_url(redis_url, socket_connect_timeout=2.0, socket_timeout=2.0, decode_responses=True)

    return make


def start_lag_metrics_server(redis_url: str, stream_name: str, port: Optional[int] = None) -> CollectorRegistry:
    """Serves /metrics on `port` (AI_WORKER_METRICS_PORT, default 9108) from a registry of its own."""
    registry = CollectorRegistry()
    registry.register(StreamLagCollector(redis_client_factory(redis_url), [stream_name]))
    start_http_server(metrics_port_from_env() if port is None else port, registry=registry)
    return registry
