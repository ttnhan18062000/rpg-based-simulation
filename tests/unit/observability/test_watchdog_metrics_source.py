"""The watchdog reads the backend's internal metrics port, and a refusing endpoint is not a stall (TCK-20261021-WATCHDOG-POLLS-AN-ADMISSION-GATED-METRICS-ENDPOINT).

These tests use the real endpoint shape: a ``prometheus_client`` registry served by ``start_metrics_port`` (the backend's 9109 server) and a small local HTTP server that answers 401 like
``/metrics`` on the API port. ``check_metrics`` itself is never patched.
"""
from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import MagicMock, patch

import pytest
from prometheus_client import CollectorRegistry, Gauge

from src.api.metrics_port import start_metrics_port
from src.observability.alerts.models import AlertEvent
from src.observability.alerts.router import AlertRouter
from src.observability.alerts.sinks import AlertSink
from src.observability.watchdog import SimulationWatchdog, parse_tick


class _Refusing(BaseHTTPRequestHandler):
    status = 401

    def do_GET(self):  # noqa: N802
        self.send_response(self.status)
        self.end_headers()
        self.wfile.write(b'{"detail":"Invalid or missing API key."}')

    def log_message(self, *args):  # silence the test server
        pass


@pytest.fixture
def refusing_server():
    """A server that answers 401 to everything, on a free local port; yields (url, handler class so a test can change the status)."""
    handler = type("Handler", (_Refusing,), {"status": 401})
    server = HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", handler
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture
def metrics_port():
    """The backend's real internal metrics server around a registry whose sim_current_tick the test sets; yields (url, set_tick)."""
    registry = CollectorRegistry()
    tick = Gauge("sim_current_tick", "Current simulation tick index", registry=registry)
    running = start_metrics_port(registry, port=0, host="127.0.0.1")
    assert running is not None
    try:
        yield f"http://127.0.0.1:{running.port}", tick.set
    finally:
        running.stop()


def _watchdog(url: str) -> SimulationWatchdog:
    watchdog = SimulationWatchdog()
    watchdog.metrics_url = url
    return watchdog


def test_it_reads_the_tick_from_the_metrics_port_and_sees_it_advance(metrics_port):
    url, set_tick = metrics_port
    watchdog = _watchdog(url)
    set_tick(5)
    assert watchdog.check_metrics() == (True, "Tick 5.0")
    set_tick(6)
    assert watchdog.check_metrics() == (True, "Tick 6.0")
    assert watchdog.metrics_blind is False


def test_a_tick_that_does_not_advance_is_a_stall(metrics_port):
    url, set_tick = metrics_port
    watchdog = _watchdog(url)
    set_tick(7)
    watchdog.check_metrics()
    assert watchdog.check_metrics() == (False, "Tick Stalled at 7.0")


def test_tick_zero_is_starting_not_a_stall(metrics_port):
    url, set_tick = metrics_port
    watchdog = _watchdog(url)
    set_tick(0)
    watchdog.check_metrics()
    assert watchdog.check_metrics() == (True, "Tick 0 (Starting)")


@pytest.mark.parametrize("status", [401, 403])
def test_a_gated_endpoint_is_blind_not_a_stall(refusing_server, status):
    url, handler = refusing_server
    handler.status = status
    watchdog = _watchdog(url)
    ok, reason = watchdog.check_metrics()
    assert ok is True and reason == f"Metrics gated (HTTP {status})"
    assert watchdog.metrics_blind is True


def test_another_error_status_is_still_a_failure(refusing_server):
    url, handler = refusing_server
    handler.status = 500
    watchdog = _watchdog(url)
    assert watchdog.check_metrics() == (False, "Metrics HTTP 500")
    assert watchdog.metrics_blind is False


def test_a_refused_connection_is_a_failure_not_blindness():
    watchdog = _watchdog("http://127.0.0.1:9")  # the discard port: nothing listens
    ok, reason = watchdog.check_metrics()
    assert ok is False and reason.startswith("Metrics Error")
    assert watchdog.metrics_blind is False


def test_the_blind_flag_clears_once_the_endpoint_answers(metrics_port, refusing_server):
    gated_url, _ = refusing_server
    url, set_tick = metrics_port
    watchdog = _watchdog(gated_url)
    watchdog.check_metrics()
    assert watchdog.metrics_blind is True
    watchdog.metrics_url = url
    set_tick(3)
    watchdog.check_metrics()
    assert watchdog.metrics_blind is False


def test_parse_tick_matches_the_exact_metric_name():
    assert parse_tick("# HELP sim_current_tick x\n# TYPE sim_current_tick gauge\nsim_current_tick 12.0\n") == 12.0
    assert parse_tick('sim_current_tick{run="a"} 4\n') == 4.0
    assert parse_tick("sim_current_tick_total 99\n") is None, "a longer name is another metric"
    assert parse_tick("other 1\n") is None
    assert parse_tick("sim_current_tick notanumber\n") is None


def _router_with_sink():
    router = AlertRouter()
    sink = MagicMock(spec=AlertSink)
    sink.send.return_value = True
    router.register_sink(sink)
    return router, sink


def test_a_gated_endpoint_raises_the_blind_alert_once_and_no_stall_alert(refusing_server):
    url, _ = refusing_server
    watchdog = _watchdog(url)
    router, sink = _router_with_sink()
    with patch.object(SimulationWatchdog, "check_health", return_value=True), \
         patch.object(SimulationWatchdog, "check_loki_errors", return_value=[]), \
         patch("src.observability.alerts.manager.AlertsManager.get_router", return_value=router):
        for _ in range(watchdog.max_failures + 3):  # well past the stall threshold
            watchdog.run_cycle()

    sent = [call.args[0] for call in sink.send.call_args_list]
    assert [a.alert_type for a in sent] == ["WatchdogBlind"], "one blind alert for the whole window (the router's dedup), and no WatchdogTrip"
    assert isinstance(sent[0], AlertEvent) and sent[0].severity == "ERROR"
    assert watchdog.consecutive_failures == 0


def test_a_real_stall_still_trips(metrics_port):
    url, set_tick = metrics_port
    watchdog = _watchdog(url)
    set_tick(10)
    router, sink = _router_with_sink()
    with patch.object(SimulationWatchdog, "check_health", return_value=True), \
         patch.object(SimulationWatchdog, "check_loki_errors", return_value=[]), \
         patch("src.observability.alerts.manager.AlertsManager.get_router", return_value=router):
        for _ in range(watchdog.max_failures + 2):  # the first cycle sees the tick advance, the rest see it stalled
            watchdog.run_cycle()
    assert "WatchdogTrip" in [call.args[0].alert_type for call in sink.send.call_args_list]
    assert "WatchdogBlind" not in [call.args[0].alert_type for call in sink.send.call_args_list]
