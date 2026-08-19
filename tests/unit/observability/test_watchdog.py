"""
Unit tests for SimulationWatchdog's critical-escalation wiring into AlertsManager
(TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC).

Covers:
- A trip (consecutive_failures >= max_failures) routes a WatchdogTrip AlertEvent to a
  registered sink, not just logger.critical().
- check_health() picks up a real run_id from /health's new `engine.run_id` field.
"""
from unittest.mock import MagicMock, patch

from src.observability.watchdog import SimulationWatchdog
from src.observability.alerts.router import AlertRouter
from src.observability.alerts.sinks import AlertSink
from src.observability.alerts.models import AlertEvent


def test_run_cycle_trip_routes_alert_event():
    watchdog = SimulationWatchdog()
    watchdog.consecutive_failures = watchdog.max_failures
    watchdog.last_tick = 42

    router = AlertRouter()
    mock_sink = MagicMock(spec=AlertSink)
    mock_sink.send.return_value = True
    router.register_sink(mock_sink)

    with patch.object(SimulationWatchdog, "check_health", return_value=False), \
         patch.object(SimulationWatchdog, "check_metrics", return_value=(True, "Tick 42")), \
         patch.object(SimulationWatchdog, "check_loki_errors", return_value=[]), \
         patch("src.observability.alerts.manager.AlertsManager.get_router", return_value=router):
        watchdog.run_cycle()

    mock_sink.send.assert_called_once()
    sent_alert = mock_sink.send.call_args[0][0]
    assert isinstance(sent_alert, AlertEvent)
    assert sent_alert.alert_type == "WatchdogTrip"
    assert sent_alert.run_id == "external-watchdog-unknown"
    assert sent_alert.tick == 42


def test_check_health_picks_up_run_id_from_health_body():
    watchdog = SimulationWatchdog()
    assert watchdog.run_id == "external-watchdog-unknown"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "ok", "engine": {"run_id": "run_123_abc"}}

    with patch("src.observability.watchdog.requests.get", return_value=mock_resp):
        result = watchdog.check_health()

    assert result is True
    assert watchdog.run_id == "run_123_abc"


def test_check_health_keeps_last_known_run_id_on_malformed_body():
    watchdog = SimulationWatchdog()
    watchdog.run_id = "run_previous"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("not json")

    with patch("src.observability.watchdog.requests.get", return_value=mock_resp):
        result = watchdog.check_health()

    assert result is True
    assert watchdog.run_id == "run_previous"
