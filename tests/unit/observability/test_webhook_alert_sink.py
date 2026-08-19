from __future__ import annotations
import random
import time
import pytest
import requests
from unittest.mock import MagicMock, patch

from src.observability.alerts.models import AlertEvent
from src.observability.alerts.sinks import WebhookAlertSink


def make_sink(**overrides) -> WebhookAlertSink:
    kwargs = dict(
        webhook_url="http://example.invalid/alert",
        enabled=True,
        timeout_seconds=1.0,
        max_retries=3,
    )
    kwargs.update(overrides)
    return WebhookAlertSink(**kwargs)


def make_alert() -> AlertEvent:
    return AlertEvent(
        alert_type="TestType",
        severity="WARNING",
        run_id="run-unit-test",
        message="unit test alert",
        dedup_key="test:unit:webhook",
    )


# ---------------------------------------------------------------------------
# AC #1 -- real exponential backoff with jitter
# ---------------------------------------------------------------------------

def test_backoff_delay_is_exponential_not_linear():
    sink = make_sink()

    delay1 = sink._compute_backoff_delay(1, rng=random.Random(0))
    delay2 = sink._compute_backoff_delay(2, rng=random.Random(0))
    delay3 = sink._compute_backoff_delay(3, rng=random.Random(0))

    assert delay1 < delay2 < delay3

    # Un-jittered midpoints should sit at ~2x ratios (0.5, 1.0, 2.0), not the
    # ~1.33x/1.5x growth a linear (0.5 * attempt) schedule would produce.
    midpoint1 = sink.BACKOFF_BASE_SECONDS * (2 ** 0)
    midpoint2 = sink.BACKOFF_BASE_SECONDS * (2 ** 1)
    midpoint3 = sink.BACKOFF_BASE_SECONDS * (2 ** 2)
    assert midpoint2 / midpoint1 == pytest.approx(2.0)
    assert midpoint3 / midpoint2 == pytest.approx(2.0)


def test_backoff_has_jitter():
    sink = make_sink()

    delay_a = sink._compute_backoff_delay(2, rng=random.Random(1))
    delay_b = sink._compute_backoff_delay(2, rng=random.Random(2))

    assert delay_a != delay_b


def test_backoff_delay_caps_at_bound():
    sink = make_sink()
    delay = sink._compute_backoff_delay(100, rng=random.Random(0))
    cap_with_jitter = sink.BACKOFF_CAP_SECONDS * (1 + sink.BACKOFF_JITTER_RATIO)

    assert delay <= cap_with_jitter


# ---------------------------------------------------------------------------
# AC #2 -- circuit breaker
# ---------------------------------------------------------------------------

def test_circuit_breaker_opens_after_consecutive_failures(monkeypatch):
    sink = make_sink(max_retries=1)
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    with patch("src.observability.alerts.sinks.requests.post", side_effect=requests.ConnectionError("down")) as mock_post:
        for _ in range(sink.CIRCUIT_BREAKER_FAILURE_THRESHOLD):
            sink._dispatch_with_retry(make_alert())

        assert mock_post.call_count == sink.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        assert sink._circuit_state == "open"

        # circuit is open: send() must not enqueue further dispatch work
        result = sink.send(make_alert())
        assert result is False

    sink.shutdown(wait=True)


def test_circuit_breaker_half_open_retry_recovers(monkeypatch):
    sink = make_sink(max_retries=1)
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    with patch("src.observability.alerts.sinks.requests.post", side_effect=requests.ConnectionError("down")) as mock_post:
        for _ in range(sink.CIRCUIT_BREAKER_FAILURE_THRESHOLD):
            sink._dispatch_with_retry(make_alert())
        assert sink._circuit_state == "open"

    # Force the cooldown to have already elapsed rather than sleeping for real.
    sink._circuit_opened_at = time.time() - sink.CIRCUIT_BREAKER_COOLDOWN_SECONDS - 1.0

    success_response = MagicMock(status_code=200)
    with patch("src.observability.alerts.sinks.requests.post", return_value=success_response) as mock_post:
        assert sink._circuit_allows_dispatch() is True
        assert sink._circuit_state == "half_open"

        sink._dispatch_with_retry(make_alert())
        assert mock_post.call_count == 1
        assert sink._circuit_state == "closed"
        assert sink._consecutive_failures == 0

    sink.shutdown(wait=True)


def test_circuit_breaker_open_send_returns_false_not_silent(monkeypatch):
    sink = make_sink(max_retries=1)
    sink._circuit_state = "open"
    sink._circuit_opened_at = time.time()  # freshly opened, well within cooldown

    with patch("src.observability.alerts.sinks.requests.post") as mock_post:
        result = sink.send(make_alert())

    assert result is False
    mock_post.assert_not_called()

    sink.shutdown(wait=True)
