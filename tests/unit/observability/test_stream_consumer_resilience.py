from __future__ import annotations
import json
import random
import pytest
from unittest.mock import MagicMock
from src.observability.events import SimulationEvent
from src.observability.stream.consumer import RedisStreamConsumer


def make_event(message: str = "test message") -> SimulationEvent:
    return SimulationEvent(
        event_type="resilience_test",
        event_category="economy",
        severity="INFO",
        source_system="test",
        message=message,
        tick=1
    )


def make_stream_payload(event: SimulationEvent) -> dict:
    return {
        "event_type": event.event_type,
        "event_category": event.event_category,
        "severity": event.severity,
        "tick": str(event.tick),
        "message": event.message,
        "payload": event.model_dump_json()
    }


def make_consumer() -> RedisStreamConsumer:
    consumer = RedisStreamConsumer(
        redis_url="redis://localhost:6379/0",
        stream_name="unit:test:stream",
        group_name="unit:test:group",
        consumer_name="unit:test:worker"
    )
    consumer.client = MagicMock()
    consumer._connected = True
    return consumer


# ---------------------------------------------------------------------------
# AC #1 -- bounded retry then DLQ
# ---------------------------------------------------------------------------

def test_handler_exception_triggers_bounded_retry_then_dlq():
    consumer = make_consumer()
    event = make_event("boom")
    msg_id = "1-1"
    payload = make_stream_payload(event)

    handler = MagicMock(side_effect=RuntimeError("transient failure"))

    # Call 1: xreadgroup delivers the message fresh (delivery attempt #1); the message is
    # too freshly-idle to appear in this same call's reclaim sweep.
    # Calls 2 and 3: no new messages; reclaim sweep finds the entry with pre-claim
    # times_delivered 1 and 2 respectively (both < MAX_DELIVERY_ATTEMPTS) and retries it
    # (delivery attempts #2 and #3).
    # Call 4: reclaim sweep finds times_delivered == MAX_DELIVERY_ATTEMPTS -- exhausted,
    # routed to DLQ, no further handler invocation.
    consumer.client.xreadgroup.side_effect = [
        [("unit:test:stream", [(msg_id, payload)])],
        None,
        None,
        None,
    ]
    consumer.client.xpending_range.side_effect = [
        [],
        [{"message_id": msg_id, "consumer": "other", "time_since_delivered": 30000, "times_delivered": 1}],
        [{"message_id": msg_id, "consumer": "other", "time_since_delivered": 30000, "times_delivered": 2}],
        [{"message_id": msg_id, "consumer": "other", "time_since_delivered": 30000, "times_delivered": 3}],
    ]
    consumer.client.xclaim.side_effect = [
        [(msg_id, payload)],
        [(msg_id, payload)],
    ]
    consumer.client.xrange.return_value = [(msg_id, payload)]

    for _ in range(4):
        consumer.read_and_process(handler, block_ms=10)

    assert handler.call_count == consumer.MAX_DELIVERY_ATTEMPTS
    assert handler.call_count == 3

    # Original message never ack'd off the source stream by the retry path itself
    # until the exhausted branch's xack call.
    dlq_calls = [
        c for c in consumer.client.xadd.call_args_list
        if c.args[0] == consumer.dlq_stream_name
    ]
    assert len(dlq_calls) == 1
    dlq_fields = dlq_calls[0].args[1]
    assert dlq_fields["payload"] == payload["payload"]
    assert dlq_fields["dlq_reason"] == "max delivery attempts exceeded"
    assert dlq_fields["dlq_source_id"] == msg_id
    assert dlq_fields["dlq_delivery_count"] == "3"
    assert "dlq_failed_at" in dlq_fields
    assert dlq_calls[0].kwargs["maxlen"] == 1000
    assert dlq_calls[0].kwargs["approximate"] is True

    xack_calls = [
        c for c in consumer.client.xack.call_args_list
        if c.args == (consumer.stream_name, consumer.group_name, msg_id)
    ]
    assert len(xack_calls) == 1


def test_send_to_dlq_writes_expected_fields():
    consumer = make_consumer()
    original_fields = {"payload": json.dumps({"a": 1}), "message": "hi"}

    result = consumer._send_to_dlq("5-0", original_fields, "max delivery attempts exceeded", 3)

    assert result is True
    consumer.client.xadd.assert_called_once()
    args, kwargs = consumer.client.xadd.call_args
    assert args[0] == consumer.dlq_stream_name
    fields = args[1]
    assert fields["payload"] == original_fields["payload"]
    assert fields["message"] == "hi"
    assert fields["dlq_reason"] == "max delivery attempts exceeded"
    assert fields["dlq_source_id"] == "5-0"
    assert fields["dlq_delivery_count"] == "3"
    assert "dlq_failed_at" in fields
    assert kwargs["maxlen"] == 1000
    assert kwargs["approximate"] is True


# ---------------------------------------------------------------------------
# AC #2 -- malformed payload stays ack+drop, never enters retry/DLQ path
# ---------------------------------------------------------------------------

def test_malformed_payload_still_ack_drop_not_retried():
    consumer = make_consumer()
    handler = MagicMock()

    acked, handler_ran = consumer._handle_message("2-0", {"payload": ""}, handler)

    assert acked is True
    assert handler_ran is False
    handler.assert_not_called()
    consumer.client.xack.assert_called_once_with(consumer.stream_name, consumer.group_name, "2-0")
    consumer.client.xadd.assert_not_called()


def test_invalid_json_payload_still_ack_drop_not_retried():
    consumer = make_consumer()
    handler = MagicMock()

    acked, handler_ran = consumer._handle_message("3-0", {"payload": "not-json"}, handler)

    assert acked is True
    assert handler_ran is False
    handler.assert_not_called()
    consumer.client.xack.assert_called_once_with(consumer.stream_name, consumer.group_name, "3-0")
    consumer.client.xadd.assert_not_called()


def test_handler_exception_leaves_message_unacked():
    consumer = make_consumer()
    event = make_event("will fail")
    payload = make_stream_payload(event)
    handler = MagicMock(side_effect=RuntimeError("boom"))

    acked, handler_ran = consumer._handle_message("4-0", payload, handler)

    assert acked is False
    assert handler_ran is True
    consumer.client.xack.assert_not_called()


# ---------------------------------------------------------------------------
# AC #4 -- reconnect backoff with jitter
# ---------------------------------------------------------------------------

def test_backoff_delay_is_pure_and_deterministic_given_seed():
    consumer = make_consumer()
    rng1 = random.Random(42)
    rng2 = random.Random(42)

    delay1 = consumer._compute_backoff_delay(3, rng=rng1)
    delay2 = consumer._compute_backoff_delay(3, rng=rng2)

    assert delay1 == delay2


def test_reconnect_backoff_increases_with_consecutive_failures():
    consumer = make_consumer()
    rng = random.Random(0)

    delay1 = consumer._compute_backoff_delay(1, rng=random.Random(0))
    delay2 = consumer._compute_backoff_delay(2, rng=random.Random(0))
    delay3 = consumer._compute_backoff_delay(3, rng=random.Random(0))

    assert delay1 < delay2 < delay3


def test_reconnect_backoff_caps_at_bound():
    consumer = make_consumer()
    delay = consumer._compute_backoff_delay(100, rng=random.Random(0))
    cap_with_jitter = consumer.BACKOFF_CAP_SECONDS * (1 + consumer.BACKOFF_JITTER_RATIO)

    assert delay <= cap_with_jitter


def test_reconnect_backoff_includes_jitter():
    consumer = make_consumer()
    delays = {
        consumer._compute_backoff_delay(4, rng=random.Random(seed))
        for seed in range(5)
    }

    assert len(delays) > 1


def test_reconnect_backoff_resets_after_success(monkeypatch):
    consumer = RedisStreamConsumer(
        redis_url="redis://localhost:6379/0",
        stream_name="unit:test:stream",
        group_name="unit:test:group",
        consumer_name="unit:test:worker"
    )

    mock_client = MagicMock()
    mock_redis_module = MagicMock()
    mock_redis_module.from_url.return_value = mock_client
    mock_redis_module.exceptions.ResponseError = Exception

    sleep_calls = []
    monkeypatch.setattr("time.sleep", lambda seconds: sleep_calls.append(seconds))

    import sys
    monkeypatch.setitem(sys.modules, "redis", mock_redis_module)

    mock_client.ping.side_effect = Exception("down")
    assert consumer.connect() is False
    assert consumer._consecutive_failures == 1

    assert consumer.connect() is False
    assert consumer._consecutive_failures == 2
    # second attempt sleeps because _consecutive_failures was > 0 going in
    assert len(sleep_calls) == 1

    mock_client.ping.side_effect = None
    mock_client.ping.return_value = True
    assert consumer.connect() is True
    assert consumer._consecutive_failures == 0

    assert consumer.connect() is True
    assert consumer._consecutive_failures == 0
    # no new sleep since failures reset to 0 after the successful connect
    assert len(sleep_calls) == 2


def test_first_connect_attempt_never_sleeps(monkeypatch):
    consumer = RedisStreamConsumer(
        redis_url="redis://localhost:6379/0",
        stream_name="unit:test:stream",
        group_name="unit:test:group",
        consumer_name="unit:test:worker"
    )

    mock_client = MagicMock()
    mock_client.ping.side_effect = Exception("down")
    mock_redis_module = MagicMock()
    mock_redis_module.from_url.return_value = mock_client
    mock_redis_module.exceptions.ResponseError = Exception

    sleep_calls = []
    monkeypatch.setattr("time.sleep", lambda seconds: sleep_calls.append(seconds))

    import sys
    monkeypatch.setitem(sys.modules, "redis", mock_redis_module)

    assert consumer.connect() is False
    assert sleep_calls == []
