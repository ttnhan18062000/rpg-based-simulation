from __future__ import annotations
import os
import tempfile
import json
import pytest
from dataclasses import dataclass, field
from typing import Dict, Any
from src.core.governance import RuntimeMode
from src.observability.reporting.metric_recorder import (
    MetricWindowRecord,
    MetricWindowAccumulator,
    MetricWindowRecorder
)

@dataclass
class MockWorldMetrics:
    tick: int = 1
    total_entities: int = 10
    alive_entities: int = 8
    total_gold: float = 1500.0
    rejection_counts: Dict[str, int] = field(default_factory=dict)
    quest_status_counts: Dict[str, int] = field(default_factory=dict)

@dataclass
class MockPressureSignals:
    tick_compute_ms: float = 12.5
    memory_estimate_mb: float = 64.0
    worker_utilization: float = 0.5
    queue_utilization: float = 0.2

@dataclass
class MockRuntimeStatus:
    current_mode: RuntimeMode = RuntimeMode.NORMAL

def test_metric_window_record_serialization() -> None:
    """Verify MetricWindowRecord compiles and serializes correctly."""
    record = MetricWindowRecord(
        run_id="test-run-123",
        window_start_tick=1,
        window_end_tick=100,
        ticks_observed=100,
        alive_entities_avg=50.0,
        active_entities_avg=60.0,
        gold_total_avg=25000.0,
        tick_compute_ms_avg=15.2,
        tick_compute_ms_p95=24.5,
        memory_rss_bytes_avg=1024.0 * 1024.0 * 128.0,
        memory_rss_bytes_max=1024.0 * 1024.0 * 150.0,
        hard_law_violation_count=2,
        event_count=50,
        anomaly_candidate_count=0
    )
    
    # Assert serializability
    serialized = record.model_dump_json()
    parsed = json.loads(serialized)
    assert parsed["run_id"] == "test-run-123"
    assert parsed["schema_version"] == "observability_metric_v1"
    assert parsed["alive_entities_avg"] == 50.0
    assert parsed["memory_rss_bytes_max"] == 1024.0 * 1024.0 * 150.0
    assert parsed["rejection_count"] == 0

def test_metric_window_accumulator_aggregation() -> None:
    """Verify MetricWindowAccumulator aggregates lists and computes correct mathematical metrics."""
    accum = MetricWindowAccumulator(run_id="test-run-abc", window_start_tick=1)
    
    # Tick 1
    world1 = MockWorldMetrics(
        total_entities=10,
        alive_entities=8,
        total_gold=100.0,
        rejection_counts={"economy": 1},
        quest_status_counts={"ACTIVE": 2, "COMPLETED": 1}
    )
    signals1 = MockPressureSignals(
        tick_compute_ms=10.0,
        memory_estimate_mb=50.0,
        worker_utilization=0.4,
        queue_utilization=0.1
    )
    status1 = MockRuntimeStatus(current_mode=RuntimeMode.NORMAL)
    
    accum.record_tick(1, world1, signals1, status1, event_count_delta=5, violation_count_delta=0)
    
    # Tick 2
    world2 = MockWorldMetrics(
        total_entities=12,
        alive_entities=9,
        total_gold=200.0,
        rejection_counts={"economy": 2, "locomotion": 1},
        quest_status_counts={"ACTIVE": 4, "COMPLETED": 1}
    )
    signals2 = MockPressureSignals(
        tick_compute_ms=20.0,
        memory_estimate_mb=100.0,
        worker_utilization=0.6,
        queue_utilization=0.3
    )
    status2 = MockRuntimeStatus(current_mode=RuntimeMode.CONSTRAINED)
    
    accum.record_tick(2, world2, signals2, status2, event_count_delta=15, violation_count_delta=2)
    
    # Flush
    record = accum.flush(2)
    
    assert record.run_id == "test-run-abc"
    assert record.window_start_tick == 1
    assert record.window_end_tick == 2
    assert record.ticks_observed == 2
    
    # Math asserts
    assert record.alive_entities_avg == 8.5   # (8 + 9) / 2
    assert record.active_entities_avg == 11.0 # (10 + 12) / 2
    assert record.gold_total_avg == 150.0     # (100 + 200) / 2
    assert record.tick_compute_ms_avg == 15.0  # (10 + 20) / 2
    
    # memory: 50MB and 100MB
    assert record.memory_rss_bytes_avg == 75.0 * 1024 * 1024
    assert record.memory_rss_bytes_max == 100.0 * 1024 * 1024
    
    # sums
    assert record.event_count == 20
    assert record.hard_law_violation_count == 2
    assert record.rejection_count == 4 # 1 + (2 + 1)
    
    # averages
    assert record.quest_active_count == 3.0 # (2 + 4) / 2
    assert record.quest_completed_count == 1.0 # (1 + 1) / 2
    assert record.worker_utilization_avg == 0.5
    assert record.queue_utilization_avg == 0.2
    
    # Dominant mode: ties are resolved by alphabetical order of max key, let's make sure it is valid
    assert record.governor_mode_dominant in ("NORMAL", "CONSTRAINED")

def test_p95_percentile_interpolation() -> None:
    """Assert deterministic p95 calculation matches percentile math."""
    accum = MetricWindowAccumulator("test", 1)
    # 20 distinct elements: 1 to 20
    values = [float(x) for x in range(1, 21)]
    p95 = accum._calculate_p95(values)
    
    # N = 20. Percentile index = (20 - 1) * 0.95 = 19 * 0.95 = 18.05
    # sorted_vals[18] = 19.0, sorted_vals[19] = 20.0
    # Interpolation = 19.0 + (20.0 - 19.0) * 0.05 = 19.05
    assert abs(p95 - 19.05) < 1e-9

def test_metric_window_recorder_lifecycle() -> None:
    """Verify MetricWindowRecorder manages window size boundaries and appends cleanly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        recorder = MetricWindowRecorder(
            run_id="run-xyz",
            run_dir=temp_dir,
            window_size=3,
            enabled=True
        )
        
        # Feed 3 ticks to trigger exact boundary flush
        for tick in range(1, 4):
            world = MockWorldMetrics(total_entities=5, alive_entities=4, total_gold=10.0 * tick)
            signals = MockPressureSignals(tick_compute_ms=5.0, memory_estimate_mb=10.0)
            status = MockRuntimeStatus(current_mode=RuntimeMode.NORMAL)
            recorder.record_tick(tick, world, signals, status, event_count_delta=2, violation_count_delta=0)
            
        # File must contain exactly 1 flushed window
        assert os.path.exists(recorder.filepath)
        with open(recorder.filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 1
        
        data = json.loads(lines[0])
        assert data["window_start_tick"] == 1
        assert data["window_end_tick"] == 3
        assert data["ticks_observed"] == 3
        assert data["gold_total_avg"] == 20.0 # (10 + 20 + 30) / 3
        
        # Feed 1 more tick (tick 4)
        world = MockWorldMetrics(total_entities=5, alive_entities=4, total_gold=40.0)
        signals = MockPressureSignals(tick_compute_ms=5.0, memory_estimate_mb=10.0)
        status = MockRuntimeStatus(current_mode=RuntimeMode.NORMAL)
        recorder.record_tick(4, world, signals, status, event_count_delta=1, violation_count_delta=0)
        
        # Shutdown to flush the partial second window
        recorder.shutdown(4)
        
        with open(recorder.filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 2
        
        data2 = json.loads(lines[1])
        assert data2["window_start_tick"] == 4
        assert data2["window_end_tick"] == 4
        assert data2["ticks_observed"] == 1
        assert data2["gold_total_avg"] == 40.0
