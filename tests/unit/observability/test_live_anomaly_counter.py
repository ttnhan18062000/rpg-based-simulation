import pytest
from src.observability.events import SimulationEvent
from src.observability.live.anomaly_counter import LiveAnomalyCounter

def test_live_anomaly_counter_singleton():
    """Verify that LiveAnomalyCounter follows the singleton pattern and reset works."""
    counter1 = LiveAnomalyCounter.get_instance()
    counter2 = LiveAnomalyCounter.get_instance()
    assert counter1 is counter2

    LiveAnomalyCounter.reset_instance()
    counter3 = LiveAnomalyCounter.get_instance()
    assert counter3 is not counter1

def test_live_anomaly_counter_increments():
    """Verify that push increments the correct counters based on event types and levels."""
    LiveAnomalyCounter.reset_instance()
    counter = LiveAnomalyCounter.get_instance()
    counter.reset()

    # 1. Normal info event
    ev1 = SimulationEvent(
        event_type="walk",
        event_category="movement",
        tick=5,
        severity="INFO",
        source_system="navigation",
        message="Actor moved",
        run_id="run-A"
    )
    counter.push(ev1)
    
    counts = counter.get_counters()
    assert counts["hard_law_violation_count"] == 0
    assert counts["navigation_stuck_count"] == 0
    assert counts["error_event_count"] == 0
    assert counts["critical_event_count"] == 0

    # 2. Hard law violation event
    ev2 = SimulationEvent(
        event_type="InvariantViolation",
        event_category="hard_law",
        tick=6,
        severity="ERROR",
        source_system="kernel",
        message="Hard law violated",
        run_id="run-A"
    )
    counter.push(ev2)
    
    counts = counter.get_counters()
    assert counts["hard_law_violation_count"] == 1
    assert counts["error_event_count"] == 1

    # 3. Stuck actor event
    ev3 = SimulationEvent(
        event_type="NavigationStuck",
        event_category="anomaly",
        tick=7,
        severity="WARNING",
        source_system="navigation",
        message="Actor stuck",
        run_id="run-A"
    )
    counter.push(ev3)
    
    counts = counter.get_counters()
    assert counts["navigation_stuck_count"] == 1
    assert counts["error_event_count"] == 1

    # 4. Critical event
    ev4 = SimulationEvent(
        event_type="crash",
        event_category="lifecycle",
        tick=8,
        severity="CRITICAL",
        source_system="system",
        message="Critical crash",
        run_id="run-A"
    )
    counter.push(ev4)
    
    counts = counter.get_counters()
    assert counts["critical_event_count"] == 1

def test_live_anomaly_counter_run_id_reset():
    """Verify that counter automatically resets when run_id changes."""
    LiveAnomalyCounter.reset_instance()
    counter = LiveAnomalyCounter.get_instance()
    counter.reset()

    ev1 = SimulationEvent(
        event_type="InvariantViolation",
        event_category="hard_law",
        tick=5,
        severity="ERROR",
        source_system="kernel",
        message="Violation run A",
        run_id="run-A"
    )
    counter.push(ev1)
    assert counter.hard_law_violation_count == 1
    assert counter.current_run_id == "run-A"

    # Push event with a different run_id
    ev2 = SimulationEvent(
        event_type="walk",
        event_category="movement",
        tick=1,
        severity="INFO",
        source_system="navigation",
        message="New run event",
        run_id="run-B"
    )
    counter.push(ev2)
    
    # Counter should be reset
    assert counter.hard_law_violation_count == 0
    assert counter.current_run_id == "run-B"
    assert counter.last_updated_tick == 1

def test_live_anomaly_counter_health_calculation():
    """Verify health state evaluation rules and alerts thresholds."""
    LiveAnomalyCounter.reset_instance()
    counter = LiveAnomalyCounter.get_instance()
    counter.reset()

    # Initial state with no manager -> UNKNOWN
    health = counter.calculate_health()
    assert health["health_state"] == "UNKNOWN"

    # Simulate errors -> WARNING
    for _ in range(2):
        counter.push(SimulationEvent(
            event_type="error_event", event_category="movement", tick=1,
            severity="ERROR", source_system="test", message="error", run_id="run-A"
        ))
    health = counter.calculate_health()
    assert health["health_state"] == "WARNING"
    assert "Tick loop errors recorded" in health["reasons"][0]

    # Stuck actors -> WARNING
    counter.reset()
    for _ in range(4):
        counter.push(SimulationEvent(
            event_type="NavigationStuck", event_category="anomaly", tick=1,
            severity="WARNING", source_system="test", message="stuck", run_id="run-A"
        ))
    health = counter.calculate_health()
    assert health["health_state"] == "WARNING"
    assert "Excessive stuck navigation events detected" in health["reasons"][0]

    # Hard law violation -> CRITICAL
    counter.reset()
    counter.push(SimulationEvent(
        event_type="InvariantViolation", event_category="hard_law", tick=1,
        severity="ERROR", source_system="test", message="hard law", run_id="run-A"
    ))
    health = counter.calculate_health()
    assert health["health_state"] == "CRITICAL"
    assert "Critical hard law violation" in health["reasons"][0]
