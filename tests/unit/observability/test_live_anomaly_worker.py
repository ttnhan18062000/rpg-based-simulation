from __future__ import annotations
import os
import json
import uuid
import shutil
import time
import pytest
from typing import List

from src.observability.events import SimulationEvent
from src.observability.anomaly.rules import (
    Anomaly,
    RollingEventWindow,
    HardLawViolationLive,
    NavigationStuckLive,
    EventDropRateHigh,
    GovernorDegradedLive,
    CriticalEventObserved
)
from src.observability.anomaly.worker import LiveWorkerConfig, LiveAnomalyWorker
from src.observability.live.event_publisher import LiveEventPublisher


def test_live_worker_config_validation():
    """Verify that LiveWorkerConfig initializes with expected default structures."""
    config = LiveWorkerConfig()
    assert config.window_ticks == 100
    assert config.stream_backend == "in_process"
    assert len(config.enabled_rules) == 5
    assert "HardLawViolationLive" in config.enabled_rules


def test_rolling_event_window_eviction():
    """Verify that event sliding window evicts expired ticks correctly."""
    window = RollingEventWindow(window_ticks=10)
    
    # Push tick 10
    ev1 = SimulationEvent(event_type="test", event_category="infrastructure", tick=10, severity="INFO", source_system="sys", message="A")
    window.push(ev1)
    assert len(window.get_all_events()) == 1
    
    # Push tick 15
    ev2 = SimulationEvent(event_type="test", event_category="infrastructure", tick=15, severity="INFO", source_system="sys", message="B")
    window.push(ev2)
    assert len(window.get_all_events()) == 2
    
    # Push tick 21 (should evict tick 10 since 21 - 10 = 11 > window_ticks=10)
    ev3 = SimulationEvent(event_type="test", event_category="infrastructure", tick=21, severity="INFO", source_system="sys", message="C")
    window.push(ev3)
    
    events = window.get_all_events()
    assert len(events) == 2
    assert ev1 not in events
    assert ev2 in events
    assert ev3 in events


def test_hard_law_violation_live_rule():
    """Verify HardLawViolationLive flags InvariantViolation events."""
    rule = HardLawViolationLive()
    window = RollingEventWindow()
    
    ev = SimulationEvent(
        event_type="InvariantViolation",
        event_category="hard_law",
        tick=5,
        severity="CRITICAL",
        source_system="hard_law_monitor",
        message="Gravity constant mutated!",
        payload={"law_id": "LAW-001"}
    )
    window.push(ev)
    
    anomalies = rule.evaluate_event(ev, window)
    assert len(anomalies) == 1
    assert anomalies[0].rule_name == "HardLawViolationLive"
    assert anomalies[0].severity == "CRITICAL"
    assert anomalies[0].tick_detected == 5


def test_navigation_stuck_live_rule():
    """Verify NavigationStuckLive flags entities that do not change position over duration."""
    rule = NavigationStuckLive(tick_threshold=5)
    window = RollingEventWindow()
    
    # Move entity 1 at tick 10 to (1.0, 2.0)
    ev1 = SimulationEvent(
        event_type="movement",
        event_category="movement",
        tick=10,
        severity="INFO",
        source_system="physics",
        entity_id=1,
        message="moving entity 1",
        payload={"end_pos": (1.0, 2.0)}
    )
    window.push(ev1)
    assert len(rule.evaluate_event(ev1, window)) == 0
    
    # Move entity 1 at tick 12 to (1.0, 2.0) (stuck for 2 ticks)
    ev2 = SimulationEvent(
        event_type="movement",
        event_category="movement",
        tick=12,
        severity="INFO",
        source_system="physics",
        entity_id=1,
        message="moving entity 1 again",
        payload={"end_pos": (1.0, 2.0)}
    )
    window.push(ev2)
    assert len(rule.evaluate_event(ev2, window)) == 0
    
    # Move entity 1 at tick 15 to (1.0, 2.0) (stuck for 5 ticks total -> triggers warning)
    ev3 = SimulationEvent(
        event_type="movement",
        event_category="movement",
        tick=15,
        severity="INFO",
        source_system="physics",
        entity_id=1,
        message="moving entity 1 again still same",
        payload={"end_pos": (1.0, 2.0)}
    )
    window.push(ev3)
    anomalies = rule.evaluate_event(ev3, window)
    assert len(anomalies) == 1
    assert anomalies[0].rule_name == "NavigationStuckLive"
    assert anomalies[0].severity == "ERROR"
    assert anomalies[0].entity_id == 1


def test_event_drop_rate_high_rule():
    """Verify EventDropRateHigh flags high publisher drop counts within window."""
    rule = EventDropRateHigh(limit_per_window=3)
    window = RollingEventWindow()
    
    ev1 = SimulationEvent(event_type="EventDropped", event_category="infrastructure", tick=1, severity="WARNING", source_system="publisher", message="dropped event log")
    ev2 = SimulationEvent(event_type="EventDropped", event_category="infrastructure", tick=2, severity="WARNING", source_system="publisher", message="dropped event log")
    ev3 = SimulationEvent(event_type="EventDropped", event_category="infrastructure", tick=3, severity="WARNING", source_system="publisher", message="dropped event log")
    
    window.push(ev1)
    assert len(rule.evaluate_event(ev1, window)) == 0
    
    window.push(ev2)
    assert len(rule.evaluate_event(ev2, window)) == 0
    
    window.push(ev3)
    anomalies = rule.evaluate_event(ev3, window)
    assert len(anomalies) == 1
    assert anomalies[0].rule_name == "EventDropRateHigh"


def test_governor_degraded_live_rule():
    """Verify GovernorDegradedLive monitors sustaining survival mode transitions."""
    rule = GovernorDegradedLive(tick_threshold=5)
    window = RollingEventWindow()
    
    # Transition to DEGRADED
    ev1 = SimulationEvent(
        event_type="GovernorModeChanged",
        event_category="infrastructure",
        tick=10,
        severity="WARNING",
        source_system="governor",
        message="degraded",
        payload={"current_mode": "DEGRADED"}
    )
    window.push(ev1)
    assert len(rule.evaluate_event(ev1, window)) == 0
    
    # A standard tick at 16 (6 ticks sustained)
    ev2 = SimulationEvent(
        event_type="tick_completed",
        event_category="infrastructure",
        tick=16,
        severity="INFO",
        source_system="kernel",
        message="tick complete"
    )
    window.push(ev2)
    anomalies = rule.evaluate_event(ev2, window)
    assert len(anomalies) == 1
    assert anomalies[0].rule_name == "GovernorDegradedLive"
    assert anomalies[0].context["sustained_ticks"] == 6


def test_critical_event_observed_rule():
    """Verify CriticalEventObserved rules catch critical notifications."""
    rule = CriticalEventObserved()
    window = RollingEventWindow()
    
    ev = SimulationEvent(
        event_type="WorkerCrashed",
        event_category="infrastructure",
        tick=1,
        severity="CRITICAL",
        source_system="worker_manager",
        message="worker thread failed unexpectedly"
    )
    window.push(ev)
    
    anomalies = rule.evaluate_event(ev, window)
    assert len(anomalies) == 1
    assert anomalies[0].severity == "CRITICAL"


def test_anomaly_deduplication_cooldown():
    """Verify that identical warnings are suppressed within a 20-tick cooldown."""
    config = LiveWorkerConfig(enabled_rules=["CriticalEventObserved"], output_mode="file")
    worker = LiveAnomalyWorker(config=config)
    
    # Seed a run
    run_id = f"test-run-{uuid.uuid4().hex[:6]}"
    
    ev1 = SimulationEvent(run_id=run_id, event_type="c", event_category="infrastructure", tick=100, severity="CRITICAL", source_system="s", message="m")
    worker.process_event(ev1)
    assert worker.anomaly_count == 1
    
    # Duplicate event within 20 ticks (tick 110) - should be deduplicated
    ev2 = SimulationEvent(run_id=run_id, event_type="c", event_category="infrastructure", tick=110, severity="CRITICAL", source_system="s", message="m")
    worker.process_event(ev2)
    assert worker.anomaly_count == 1
    
    # Duplicate event after 20 ticks (tick 125) - should alert again
    ev3 = SimulationEvent(run_id=run_id, event_type="c", event_category="infrastructure", tick=125, severity="CRITICAL", source_system="s", message="m")
    worker.process_event(ev3)
    assert worker.anomaly_count == 2
    
    # Cleanup generated files
    shutil.rmtree(os.path.join(worker.repo.base_dir, run_id), ignore_errors=True)


def test_worker_lifecycle_in_process():
    """Verify the start, process loop, heartbeat status flush, and stop transitions in-process."""
    # Reset singleton to prevent leaks
    LiveEventPublisher.reset_instance()
    
    config = LiveWorkerConfig(
        stream_backend="in_process",
        enabled_rules=["CriticalEventObserved"],
        output_mode="file"
    )
    worker = LiveAnomalyWorker(config=config)
    
    # Verify pending state
    assert worker.status_record.status == "PENDING"
    
    # Start worker background thread
    worker.start()
    time.sleep(0.2)
    assert worker.status_record.status == "RUNNING"
    
    # Publish CRITICAL event in-process
    run_id = f"test-run-{uuid.uuid4().hex[:6]}"
    ev = SimulationEvent(
        run_id=run_id,
        event_type="test",
        event_category="infrastructure",
        tick=50,
        severity="CRITICAL",
        source_system="sys",
        message="System failure!"
    )
    LiveEventPublisher.get_instance().publish(ev)
    
    # Wait for background thread processing
    time.sleep(0.5)
    
    assert worker.processed_count == 1
    assert worker.anomaly_count == 1
    assert worker.last_event_tick == 50
    assert worker.status_record.current_run_id == run_id
    
    # Stop worker cleanly
    worker.stop()
    assert worker.status_record.status == "STOPPED"
    
    # Verify generated anomaly file exists
    anomaly_file = os.path.join(worker.repo.base_dir, run_id, "anomaly_events.jsonl")
    assert os.path.exists(anomaly_file)
    with open(anomaly_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["rule_name"] == "CriticalEventObserved"
        
    # Cleanup files
    shutil.rmtree(os.path.join(worker.repo.base_dir, run_id), ignore_errors=True)
