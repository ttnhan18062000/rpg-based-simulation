"""
Unit tests for the Alert Routing system (Milestone 40).

Covers:
- AlertEvent instantiation and JSON serialization
- AlertEvent factory methods (hard law, watchdog, critical anomaly, backpressure)
- AlertDeduplicator sliding-window suppression and TTL expiry
- AlertRouter routing, severity filtering, sink dispatch, and metrics
- LogAlertSink formatting and output
"""
import json
import time
import logging
import pytest
from unittest.mock import MagicMock, patch

from src.observability.alerts.models import AlertEvent
from src.observability.alerts.deduplicator import AlertDeduplicator
from src.observability.alerts.sinks import AlertSink, LogAlertSink, WebhookAlertSink
from src.observability.alerts.router import AlertRouter


# ── AlertEvent Tests ──────────────────────────────────────────────────────

class TestAlertEvent:
    def test_creation_default_fields(self):
        evt = AlertEvent(
            alert_type="HardLawViolation",
            severity="CRITICAL",
            run_id="run-001",
            message="Gold went negative",
            dedup_key="hard_law:gold_non_negative:42"
        )
        assert evt.alert_type == "HardLawViolation"
        assert evt.severity == "CRITICAL"
        assert evt.run_id == "run-001"
        assert evt.message == "Gold went negative"
        assert evt.dedup_key == "hard_law:gold_non_negative:42"
        assert evt.sweep_id is None
        assert evt.tick is None
        assert evt.evidence == {}
        assert len(evt.alert_id) == 36  # uuid4 format
        assert "T" in evt.created_at  # ISO-8601 format

    def test_to_dict_serialization(self):
        evt = AlertEvent(
            alert_type="WatchdogTrip",
            severity="CRITICAL",
            run_id="run-002",
            message="Budget exceeded",
            dedup_key="watchdog:run-002",
            tick=500,
            evidence={"compute_ms": 120.5}
        )
        d = evt.to_dict()
        assert isinstance(d, dict)
        assert d["alert_type"] == "WatchdogTrip"
        assert d["tick"] == 500
        assert d["evidence"]["compute_ms"] == 120.5
        # Must be JSON-serializable
        json_str = json.dumps(d)
        assert "WatchdogTrip" in json_str

    def test_factory_hard_law_violation(self):
        violation = MagicMock()
        violation.law_id = "gold_non_negative"
        violation.entity_id = 42
        violation.message = "Gold went negative"
        violation.severity = "CRITICAL"
        violation.details = {"gold": -10}

        evt = AlertEvent.create_hard_law_violation("run-003", 100, violation)
        assert evt.alert_type == "HardLawViolation"
        assert evt.severity == "CRITICAL"
        assert evt.run_id == "run-003"
        assert evt.tick == 100
        assert "gold_non_negative" in evt.dedup_key
        assert evt.evidence["law_id"] == "gold_non_negative"

    def test_factory_watchdog_trip(self):
        evt = AlertEvent.create_watchdog_trip(
            "run-004", 200, "Budget exceeded", {"compute_ms": 150.0}
        )
        assert evt.alert_type == "WatchdogTrip"
        assert evt.severity == "CRITICAL"
        assert evt.tick == 200
        assert "watchdog" in evt.dedup_key

    def test_factory_critical_anomaly(self):
        evt = AlertEvent.create_critical_anomaly(
            "run-005", 300, "Navigation stuck",
            {"rule_id": "NavigationStuckLive", "entity_id": 7}
        )
        assert evt.alert_type == "CriticalAnomaly"
        assert evt.severity == "ERROR"
        assert "NavigationStuckLive" in evt.dedup_key

    def test_factory_stream_backpressure(self):
        evt = AlertEvent.create_stream_backpressure(
            "run-006", 400, "50 events dropped",
            {"dropped_count": 50}
        )
        assert evt.alert_type == "StreamBackpressureHigh"
        assert evt.severity == "WARNING"
        assert "backpressure" in evt.dedup_key


# ── AlertDeduplicator Tests ──────────────────────────────────────────────

class TestAlertDeduplicator:
    def test_first_alert_not_suppressed(self):
        dedup = AlertDeduplicator(suppression_window_seconds=60.0)
        assert dedup.should_suppress("key-A", current_time=1000.0) is False

    def test_duplicate_within_window_suppressed(self):
        dedup = AlertDeduplicator(suppression_window_seconds=60.0)
        dedup.should_suppress("key-B", current_time=1000.0)
        assert dedup.should_suppress("key-B", current_time=1030.0) is True

    def test_duplicate_after_window_not_suppressed(self):
        dedup = AlertDeduplicator(suppression_window_seconds=10.0)
        dedup.should_suppress("key-C", current_time=1000.0)
        # After 10 seconds the key should have expired
        assert dedup.should_suppress("key-C", current_time=1011.0) is False

    def test_different_keys_not_suppressed(self):
        dedup = AlertDeduplicator(suppression_window_seconds=60.0)
        dedup.should_suppress("key-D", current_time=1000.0)
        assert dedup.should_suppress("key-E", current_time=1000.0) is False

    def test_prune_clears_expired(self):
        dedup = AlertDeduplicator(suppression_window_seconds=5.0)
        dedup.should_suppress("key-F", current_time=100.0)
        dedup.should_suppress("key-G", current_time=102.0)
        assert dedup.seen_count == 2
        dedup.prune(current_time=106.0)
        assert dedup.seen_count == 1  # key-F expired, key-G still alive

    def test_clear_empties_all(self):
        dedup = AlertDeduplicator()
        dedup.should_suppress("key-H")
        dedup.should_suppress("key-I")
        dedup.clear()
        assert dedup.seen_count == 0


# ── LogAlertSink Tests ───────────────────────────────────────────────────

class TestLogAlertSink:
    def test_log_sink_returns_true(self):
        sink = LogAlertSink()
        evt = AlertEvent(
            alert_type="TestType",
            severity="WARNING",
            run_id="run-log",
            message="Test log message",
            dedup_key="test:log"
        )
        assert sink.send(evt) is True

    def test_log_sink_uses_correct_log_level(self, caplog):
        sink = LogAlertSink()
        evt = AlertEvent(
            alert_type="TestType",
            severity="CRITICAL",
            run_id="run-log-crit",
            message="Critical test alert",
            dedup_key="test:log:crit"
        )
        with caplog.at_level(logging.CRITICAL, logger="src.observability.alerts.sinks"):
            sink.send(evt)
        assert "Critical test alert" in caplog.text


# ── AlertRouter Tests ────────────────────────────────────────────────────

class TestAlertRouter:
    def _make_alert(self, severity="WARNING", dedup_key="test:key"):
        return AlertEvent(
            alert_type="TestAlert",
            severity=severity,
            run_id="run-router",
            message="Router test",
            dedup_key=dedup_key
        )

    def test_routes_to_registered_sink(self):
        router = AlertRouter()
        mock_sink = MagicMock(spec=AlertSink)
        mock_sink.send.return_value = True
        router.register_sink(mock_sink)

        alert = self._make_alert()
        result = router.route(alert)
        assert result is True
        mock_sink.send.assert_called_once_with(alert)

    def test_severity_threshold_filters_low(self):
        router = AlertRouter(severity_threshold="ERROR")
        mock_sink = MagicMock(spec=AlertSink)
        router.register_sink(mock_sink)

        # WARNING < ERROR threshold => should be filtered out
        alert = self._make_alert(severity="WARNING")
        result = router.route(alert)
        assert result is False
        mock_sink.send.assert_not_called()

    def test_severity_threshold_passes_high(self):
        router = AlertRouter(severity_threshold="WARNING")
        mock_sink = MagicMock(spec=AlertSink)
        mock_sink.send.return_value = True
        router.register_sink(mock_sink)

        alert = self._make_alert(severity="CRITICAL")
        result = router.route(alert)
        assert result is True
        mock_sink.send.assert_called_once()

    def test_deduplication_suppresses_repeat(self):
        router = AlertRouter()
        mock_sink = MagicMock(spec=AlertSink)
        mock_sink.send.return_value = True
        router.register_sink(mock_sink)

        alert1 = self._make_alert(dedup_key="dup:test")
        alert2 = self._make_alert(dedup_key="dup:test")
        router.route(alert1)
        router.route(alert2)
        # Only first alert should have been dispatched
        assert mock_sink.send.call_count == 1

    def test_different_dedup_keys_both_dispatch(self):
        router = AlertRouter()
        mock_sink = MagicMock(spec=AlertSink)
        mock_sink.send.return_value = True
        router.register_sink(mock_sink)

        alert1 = self._make_alert(dedup_key="key:alpha")
        alert2 = self._make_alert(dedup_key="key:beta")
        router.route(alert1)
        router.route(alert2)
        assert mock_sink.send.call_count == 2

    def test_metrics_tracking(self):
        router = AlertRouter()
        mock_sink = MagicMock(spec=AlertSink)
        mock_sink.send.return_value = True
        router.register_sink(mock_sink)

        router.route(self._make_alert(dedup_key="m1"))
        router.route(self._make_alert(dedup_key="m1"))  # suppressed
        router.route(self._make_alert(dedup_key="m2"))

        m = router.metrics
        assert m["routed_total"] == 2
        assert m["suppressed_total"] == 1
        assert m["delivered_total"] == 2

    def test_sink_exception_does_not_crash(self):
        router = AlertRouter()
        bad_sink = MagicMock(spec=AlertSink)
        bad_sink.send.side_effect = RuntimeError("Sink exploded")
        router.register_sink(bad_sink)

        alert = self._make_alert(dedup_key="crash:test")
        # Should not raise
        result = router.route(alert)
        assert result is False
        assert router.metrics["failures_total"] == 1

    def test_unregister_sink(self):
        router = AlertRouter()
        sink = MagicMock(spec=AlertSink)
        sink.send.return_value = True
        router.register_sink(sink)
        router.unregister_sink(sink)

        router.route(self._make_alert(dedup_key="unreg:test"))
        sink.send.assert_not_called()

    def test_reset_metrics(self):
        router = AlertRouter()
        mock_sink = MagicMock(spec=AlertSink)
        mock_sink.send.return_value = True
        router.register_sink(mock_sink)
        router.route(self._make_alert(dedup_key="reset:test"))

        router.reset_metrics()
        m = router.metrics
        assert m["routed_total"] == 0
        assert m["delivered_total"] == 0
