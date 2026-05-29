import time
import pytest
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.performance.models import PhaseTimingRecord
from src.observability.performance.profiler import PhaseProfiler, PhaseProfileScope

@pytest.fixture(autouse=True)
def cleanup_overrides():
    ObservabilityConfig.clear_all_overrides()
    yield
    ObservabilityConfig.clear_all_overrides()

def test_phase_timing_record_initialization():
    record = PhaseTimingRecord(
        run_id="test_run",
        tick=42,
        phase_name="combat",
        duration_ns=1000000,
        entity_count=5,
        update_count=10,
        event_count=3,
        budget_status="OK",
        failed=False
    )
    assert record.run_id == "test_run"
    assert record.tick == 42
    assert record.phase_name == "combat"
    assert record.duration_ns == 1000000
    assert record.entity_count == 5
    assert record.update_count == 10
    assert record.event_count == 3
    assert record.budget_status == "OK"
    assert record.failed is False

def test_phase_profiler_and_scope_execution():
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    profiler = PhaseProfiler(run_id="test_run_1")
    
    assert len(profiler.records) == 0
    
    with profiler.profile_phase(tick=1, phase_name="movement") as scope:
        time.sleep(0.01) # Sleep to simulate execution time
        scope.set_counter("entity_count", 8)
        scope.inc_counter("event_count", 2)
        scope.inc_counter("event_count", 3)
        scope.set_counter("budget_status", "WARNING")
        
    assert len(profiler.records) == 1
    record = profiler.records[0]
    
    assert record.run_id == "test_run_1"
    assert record.tick == 1
    assert record.phase_name == "movement"
    assert record.duration_ns > 0
    assert record.entity_count == 8
    assert record.event_count == 5
    assert record.budget_status == "WARNING"
    assert record.failed is False

def test_phase_profiler_exception_safety():
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    profiler = PhaseProfiler(run_id="test_run_2")
    
    with pytest.raises(ValueError):
        with profiler.profile_phase(tick=2, phase_name="econ") as scope:
            scope.set_counter("entity_count", 3)
            raise ValueError("Simulated Phase Failure")
            
    assert len(profiler.records) == 1
    record = profiler.records[0]
    assert record.phase_name == "econ"
    assert record.entity_count == 3
    assert record.failed is True

def test_phase_profiler_disabled_near_zero_overhead():
    # Set mode to OFF, which disables OBS_RUNTIME_PROFILING
    ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)
    profiler = PhaseProfiler(run_id="test_run_3")
    
    with profiler.profile_phase(tick=3, phase_name="progression") as scope:
        scope.set_counter("entity_count", 10)
        scope.inc_counter("event_count", 5)
        
    assert len(profiler.records) == 0

