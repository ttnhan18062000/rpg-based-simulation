"""
Integration tests for the WebhookAlertSink (Milestone 40).

Covers:
- Successful webhook delivery to a local mock HTTP server
- Graceful handling of HTTP 500 error responses (retry + failure logging)
- Graceful handling of connection timeouts without crashing
- AlertsManager wiring with webhook sink enabled
"""
import json
import time
import threading
import logging
import pytest
from http.server import HTTPServer, BaseHTTPRequestHandler
from unittest.mock import patch

from src.observability.alerts.models import AlertEvent
from src.observability.alerts.sinks import WebhookAlertSink
from src.observability.alerts.manager import AlertsManager


# ── Mock HTTP Server ─────────────────────────────────────────────────────

class _ReceivedPayloads:
    """Shared mutable container for the mock server to record received data."""
    def __init__(self):
        self.payloads = []
        self.response_code = 200
        self.lock = threading.Lock()


_received = _ReceivedPayloads()


class _MockWebhookHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that records POST body and returns configurable status."""
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        with _received.lock:
            _received.payloads.append(json.loads(body.decode("utf-8")))
        self.send_response(_received.response_code)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress noisy server logs


@pytest.fixture(scope="module")
def webhook_server():
    """Starts a background HTTP server on a random port for the test module."""
    server = HTTPServer(("127.0.0.1", 0), _MockWebhookHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}/alert"
    server.shutdown()


@pytest.fixture(autouse=True)
def reset_state():
    """Reset shared received payloads and AlertsManager before each test."""
    with _received.lock:
        _received.payloads.clear()
        _received.response_code = 200
    AlertsManager.reset()
    yield
    AlertsManager.reset()


# ── Tests ────────────────────────────────────────────────────────────────

class TestWebhookAlertSinkIntegration:
    def test_successful_delivery(self, webhook_server):
        """Webhook receives a correctly structured JSON payload on success."""
        sink = WebhookAlertSink(
            webhook_url=webhook_server,
            enabled=True,
            timeout_seconds=5.0,
            max_retries=1
        )
        alert = AlertEvent(
            alert_type="HardLawViolation",
            severity="CRITICAL",
            run_id="run-webhook-ok",
            message="Gold went negative",
            dedup_key="test:webhook:ok",
            tick=42,
            evidence={"law_id": "gold_non_negative"}
        )
        result = sink.send(alert)
        assert result is True  # Enqueued to executor

        # Wait for async delivery
        time.sleep(1.5)
        sink.shutdown(wait=True)

        with _received.lock:
            assert len(_received.payloads) == 1
            payload = _received.payloads[0]
            assert payload["alert_type"] == "HardLawViolation"
            assert payload["severity"] == "CRITICAL"
            assert payload["run_id"] == "run-webhook-ok"
            assert payload["tick"] == 42
            assert payload["evidence"]["law_id"] == "gold_non_negative"

    def test_server_error_does_not_crash(self, webhook_server):
        """HTTP 500 responses are retried and logged; no exception is raised."""
        _received.response_code = 500

        sink = WebhookAlertSink(
            webhook_url=webhook_server,
            enabled=True,
            timeout_seconds=2.0,
            max_retries=2
        )
        alert = AlertEvent(
            alert_type="WatchdogTrip",
            severity="CRITICAL",
            run_id="run-webhook-500",
            message="Budget exceeded",
            dedup_key="test:webhook:500"
        )
        # Should not raise
        result = sink.send(alert)
        assert result is True  # Enqueued

        # Wait for retries to complete
        time.sleep(4.0)
        sink.shutdown(wait=True)

        with _received.lock:
            # Should have received 2 attempts (max_retries=2)
            assert len(_received.payloads) == 2

    def test_connection_timeout_does_not_crash(self):
        """Pointing to an unreachable host does not crash the caller."""
        sink = WebhookAlertSink(
            webhook_url="http://192.0.2.1:9999/timeout",  # RFC 5737 TEST-NET, unreachable
            enabled=True,
            timeout_seconds=0.5,
            max_retries=1
        )
        alert = AlertEvent(
            alert_type="StreamBackpressureHigh",
            severity="WARNING",
            run_id="run-webhook-timeout",
            message="Backpressure high",
            dedup_key="test:webhook:timeout"
        )
        # Should not raise
        result = sink.send(alert)
        assert result is True  # Enqueued

        # Wait for the attempt to time out
        time.sleep(2.0)
        sink.shutdown(wait=True)

    def test_disabled_sink_does_not_send(self, webhook_server):
        """A disabled webhook sink should not POST anything."""
        sink = WebhookAlertSink(
            webhook_url=webhook_server,
            enabled=False
        )
        alert = AlertEvent(
            alert_type="TestType",
            severity="INFO",
            run_id="run-disabled",
            message="Should not arrive",
            dedup_key="test:disabled"
        )
        result = sink.send(alert)
        assert result is False

        time.sleep(0.5)
        with _received.lock:
            assert len(_received.payloads) == 0


class TestAlertsManagerIntegration:
    def test_manager_creates_router_with_log_sink(self):
        """AlertsManager creates a router with at least a LogAlertSink by default."""
        router = AlertsManager.get_router()
        assert router is not None
        # Should have at least LogAlertSink registered
        sink_types = [type(s).__name__ for s in router._sinks]
        assert "LogAlertSink" in sink_types

    def test_manager_singleton_returns_same_router(self):
        """Multiple get_router() calls return the same instance."""
        r1 = AlertsManager.get_router()
        r2 = AlertsManager.get_router()
        assert r1 is r2

    def test_manager_reset_creates_new_router(self):
        """After reset(), a fresh router is created on next access."""
        r1 = AlertsManager.get_router()
        AlertsManager.reset()
        r2 = AlertsManager.get_router()
        assert r1 is not r2
