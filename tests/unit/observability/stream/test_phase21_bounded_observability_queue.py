import pytest
from src.observability.events import ObservabilityEventEnvelope
from src.observability.queue import BoundedObservabilityQueue, PushStatus

def _create_mock_envelope(event_id: str, severity: str) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=event_id,
        run_id="test_run",
        tick=1,
        entity_id=101,
        event_type="test_event",
        event_category="combat",
        severity=severity,
        source_system="test_system",
        message="Mock event message"
    )

def test_queue_push_success():
    queue = BoundedObservabilityQueue(max_size=3)
    
    status = queue.try_push(_create_mock_envelope("ev1", "INFO"))
    assert status == PushStatus.SUCCESS
    assert queue.get_size() == 1
    
    queue.try_push(_create_mock_envelope("ev2", "WARNING"))
    assert queue.get_size() == 2

def test_queue_drops_low_priority_when_full():
    queue = BoundedObservabilityQueue(max_size=2)
    
    queue.try_push(_create_mock_envelope("ev1", "INFO"))
    queue.try_push(_create_mock_envelope("ev2", "INFO"))
    
    # Push another low priority event when full
    status = queue.try_push(_create_mock_envelope("ev3", "INFO"))
    assert status == PushStatus.DROPPED
    assert queue.get_size() == 2
    assert queue.dropped_count == 1

def test_queue_keeps_high_priority_and_evicts_low_priority_when_full():
    queue = BoundedObservabilityQueue(max_size=2)
    
    queue.try_push(_create_mock_envelope("ev1", "INFO"))
    queue.try_push(_create_mock_envelope("ev2", "INFO"))
    
    # Push a CRITICAL high-priority event when full
    status = queue.try_push(_create_mock_envelope("ev3", "CRITICAL"))
    assert status == PushStatus.SUCCESS
    assert queue.get_size() == 2
    assert queue.dropped_count == 1
    
    # Evicted the oldest low-priority event ("ev1")
    drained = queue.drain()
    ids = [env.event_id for env in drained]
    assert "ev1" not in ids
    assert "ev2" in ids
    assert "ev3" in ids

def test_queue_rejects_new_high_priority_when_completely_full_of_high_priority():
    queue = BoundedObservabilityQueue(max_size=2)
    
    queue.try_push(_create_mock_envelope("ev1", "CRITICAL"))
    queue.try_push(_create_mock_envelope("ev2", "ERROR"))
    
    # Try to push another CRITICAL event when all items are high priority
    status = queue.try_push(_create_mock_envelope("ev3", "CRITICAL"))
    assert status == PushStatus.REJECTED
    assert queue.get_size() == 2
    
    drained = queue.drain()
    ids = [env.event_id for env in drained]
    assert "ev1" in ids
    assert "ev2" in ids
    assert "ev3" not in ids
