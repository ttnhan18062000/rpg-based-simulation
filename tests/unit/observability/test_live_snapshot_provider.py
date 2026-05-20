from __future__ import annotations
import time
import pytest
from src.observability.live.snapshot_provider import LiveSnapshotProvider, LiveRunStatus, LiveRunSnapshot

def test_live_snapshot_provider_idle():
    # Test provider when manager is None
    status = LiveSnapshotProvider.get_status(None)
    assert isinstance(status, LiveRunStatus)
    assert status.status == "IDLE"
    assert status.health_state == "UNKNOWN"
    assert status.elapsed_seconds == 0.0
    assert status.run_id is None
    
    snapshot = LiveSnapshotProvider.get_snapshot(None)
    assert isinstance(snapshot, LiveRunSnapshot)
    assert snapshot.run_status.status == "IDLE"
    assert len(snapshot.latest_world_metrics) == 0
    assert len(snapshot.latest_runtime_status) == 0

class DummyEventRecorder:
    def __init__(self):
        self.event_count_by_type = {"combat_swing": 5, "quest_accepted": 2}

class DummyKernelStatus:
    def __init__(self):
        from src.core.governance import RuntimeMode
        self.current_mode = RuntimeMode.NORMAL
        self.last_hard_law_violation_tick = 42
        self.cumulative_violations = {"COMBAT-017": 1}

class DummyKernel:
    def __init__(self):
        self.run_id = "test-run-123"
        self.event_recorder = DummyEventRecorder()
        self.status = DummyKernelStatus()

class DummyEngineManager:
    def __init__(self):
        self.is_running = True
        self.is_paused = False
        self.is_stopped = False
        self.is_stopping = False
        self.tick = 100
        self.started_at = time.time() - 10.0
        self.kernel = DummyKernel()
        self.errors_total = 0
        
        self.metrics_snapshot = {
            "active_entities": 15,
            "gold_circulation_total": 5000.0,
            "rejection_counts": {},
            "quest_status_counts": {"active": 2},
            "tps": 20.0,
            "tick_compute_ms": 1.5,
            "worker_utilization": 0.12,
            "queue_utilization": 0.05,
            "memory_rss_bytes": 45000000.0,
            "work_debt_total": 0,
            "dropped_work_delta": 0,
            "errors_total": 0,
            "phase_costs_ms": {"combat": 0.5},
            "hard_law_violations_cumulative": {"COMBAT-017": 1},
            "last_hard_law_violation_tick": 42,
        }
        
    def get_metrics_snapshot(self):
        return self.metrics_snapshot

def test_live_snapshot_provider_active():
    manager = DummyEngineManager()
    
    # 1. Test status mapping
    status = LiveSnapshotProvider.get_status(manager)
    assert status.status == "RUNNING"
    assert status.run_id == "test-run-123"
    assert status.current_tick == 100
    assert status.governor_mode == "NORMAL"
    # Cumulative violations count > 0 should make health state CRITICAL
    assert status.health_state == "CRITICAL"
    assert status.last_hard_law_violation_tick == 42
    assert status.elapsed_seconds > 9.0
    
    # 2. Test status mapping when paused
    manager.is_running = False
    manager.is_paused = True
    status_paused = LiveSnapshotProvider.get_status(manager)
    assert status_paused.status == "PAUSED"
    
    # 3. Test complete snapshot mapping
    manager.is_running = True
    manager.is_paused = False
    snapshot = LiveSnapshotProvider.get_snapshot(manager)
    assert snapshot.run_status.status == "RUNNING"
    assert snapshot.latest_world_metrics["active_entities"] == 15
    assert snapshot.latest_world_metrics["gold_circulation_total"] == 5000.0
    assert snapshot.latest_runtime_status["tps"] == 20.0
    assert snapshot.latest_runtime_status["tick_compute_ms"] == 1.5
    assert snapshot.latest_runtime_status["memory_rss_bytes"] == 45000000.0
    assert snapshot.latest_runtime_status["phase_costs_ms"]["combat"] == 0.5
    assert snapshot.recent_event_counts["combat_swing"] == 5
    assert snapshot.recent_anomaly_counts["COMBAT-017"] == 1
    assert snapshot.hard_law_violation_count == 1
