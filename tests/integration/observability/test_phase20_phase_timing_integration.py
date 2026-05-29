import os
import json
import pytest
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.performance.models import PhaseTimingRecord
from src.observability.performance.profiler import PhaseProfiler
from src.observability.reporting.metric_recorder import MetricWindowRecorder, MetricWindowAccumulator

@pytest.fixture(autouse=True)
def cleanup_overrides():
    ObservabilityConfig.clear_all_overrides()
    yield
    ObservabilityConfig.clear_all_overrides()

def test_phase_timing_accumulation_and_flush():
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    
    accumulator = MetricWindowAccumulator(run_id="test_integration_run", window_start_tick=1)
    profiler = PhaseProfiler(run_id="test_integration_run")
    
    # 1. Simulate tick 1
    # Run the simulation phases with the profiler
    with profiler.profile_phase(tick=1, phase_name="combat") as scope:
        scope.set_counter("entity_count", 4)
        scope.set_counter("event_count", 2)
        scope.set_counter("budget_status", "OK")
        
    with profiler.profile_phase(tick=1, phase_name="movement") as scope:
        scope.set_counter("entity_count", 4)
        scope.set_counter("event_count", 1)
        scope.set_counter("budget_status", "OK")
        
    # Record tick 1 core metrics
    accumulator.record_tick(
        tick=1,
        world_metrics=None,
        pressure_signals=None,
        runtime_status=None,
        event_count_delta=3,
        violation_count_delta=0
    )
    
    # Record Phase 20 profiling timings for tick 1
    accumulator.record_profile_metrics(
        phase_records=profiler.records,
        observability_overhead_ms=0.5,
        event_emission_ms=0.1
    )
    profiler.clear() # Clear profiler records for next tick
    
    # 2. Simulate tick 2
    with profiler.profile_phase(tick=2, phase_name="combat") as scope:
        scope.set_counter("entity_count", 5)
        scope.set_counter("event_count", 3)
        scope.set_counter("budget_status", "WARNING")
        
    accumulator.record_tick(
        tick=2,
        world_metrics=None,
        pressure_signals=None,
        runtime_status=None,
        event_count_delta=3,
        violation_count_delta=0
    )
    accumulator.record_profile_metrics(
        phase_records=profiler.records,
        observability_overhead_ms=0.7,
        event_emission_ms=0.2
    )
    
    # 3. Flush the accumulator
    record = accumulator.flush(end_tick=2)
    
    assert record.ticks_observed == 2
    assert record.observability_overhead_ms_avg == pytest.approx(0.6)
    assert record.event_emission_ms_avg == pytest.approx(0.15)

    
    # Parse and verify phase timing averages
    assert record.phase_duration_ms_avg_json is not None
    avg_timings = json.loads(record.phase_duration_ms_avg_json)
    
    assert "combat" in avg_timings
    assert "movement" in avg_timings
    assert avg_timings["combat"] > 0
    assert avg_timings["movement"] > 0
    
    # Verify phase budget dominant status
    assert record.phase_budget_status_json is not None
    budgets = json.loads(record.phase_budget_status_json)
    # combat should be "WARNING" dominant or "OK" depending on count/freq, since both "OK" and "WARNING" occurred once, dominant resolved deterministic max
    assert "combat" in budgets
    assert budgets["movement"] == "OK"
