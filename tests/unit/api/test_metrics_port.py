"""The backend's internal metrics port (issue #622, R1): serves a registry without auth, takes its port from BACKEND_METRICS_PORT, and a port that cannot be bound never raises."""
from __future__ import annotations

import socket
import urllib.request

from prometheus_client import CollectorRegistry, Gauge

from src.api.metrics_port import (
    DEFAULT_METRICS_HOST, DEFAULT_METRICS_PORT, METRICS_HOST_ENV, METRICS_PORT_ENV, metrics_host_from_env, metrics_port_from_env, start_metrics_port,
)


def _registry() -> CollectorRegistry:
    registry = CollectorRegistry()
    Gauge("sim_probe_value", "A probe gauge", registry=registry).set(7)
    return registry


def test_the_port_serves_the_registry_at_metrics_without_any_credential():
    handle = start_metrics_port(_registry(), port=0)
    assert handle is not None
    try:
        request = urllib.request.Request(f"http://127.0.0.1:{handle.port}/metrics")  # no X-API-Key, no Authorization
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode()
            assert response.status == 200
    finally:
        handle.stop()
    assert "sim_probe_value 7.0" in body


def test_the_default_port_is_9109_and_the_environment_overrides_it():
    assert DEFAULT_METRICS_PORT == 9109
    assert metrics_port_from_env({}) == 9109
    assert metrics_port_from_env({METRICS_PORT_ENV: "9200"}) == 9200
    assert metrics_port_from_env({METRICS_PORT_ENV: " "}) == 9109


def test_an_unusable_value_falls_back_to_the_default():
    for bad in ("nine", "-1", "70000"):
        assert metrics_port_from_env({METRICS_PORT_ENV: bad}) == 9109


def test_a_port_that_cannot_be_bound_is_logged_and_not_raised():
    with socket.socket() as taken:
        taken.bind(("0.0.0.0", 0))
        taken.listen(1)
        assert start_metrics_port(_registry(), port=taken.getsockname()[1]) is None


def test_the_server_stops_and_releases_its_port():
    handle = start_metrics_port(_registry(), port=0)
    port = handle.port
    handle.stop()
    again = start_metrics_port(_registry(), port=port)
    assert again is not None
    again.stop()


def test_the_host_defaults_to_every_interface_and_the_environment_can_narrow_it():
    assert DEFAULT_METRICS_HOST == "0.0.0.0"
    assert metrics_host_from_env({}) == "0.0.0.0"
    assert metrics_host_from_env({METRICS_HOST_ENV: " "}) == "0.0.0.0"
    assert metrics_host_from_env({METRICS_HOST_ENV: "127.0.0.1"}) == "127.0.0.1"


def test_a_loopback_host_is_served_on_loopback_only():
    handle = start_metrics_port(_registry(), port=0, host="127.0.0.1")
    assert handle is not None
    try:
        assert handle._server.server_address[0] == "127.0.0.1"
        with urllib.request.urlopen(f"http://127.0.0.1:{handle.port}/metrics", timeout=5) as response:
            assert response.status == 200
    finally:
        handle.stop()
