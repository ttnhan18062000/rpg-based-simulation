import pytest
import time
from unittest.mock import MagicMock
from src.perf.bench_harness import BenchHarness
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG
from src.config.profiles import RuntimeProfile

from src.perf.profiles import PERF_PROFILES

@pytest.fixture
def base_state():
    return AuthoritativeState(tick=1, seed=42)

@pytest.fixture
def profile():
    return PERF_PROFILES["PERF_512MB_LOCAL"]

def test_benchmark_disables_replay_by_default(base_state, profile):
    """
    Law:
        BenchHarness must not include replay/hash overhead unless explicitly requested.
    """
    harness = BenchHarness(profile)
    # Use a small number of ticks
    result = harness.run_benchmark(
        scenario_id="TEST",
        initial_state=base_state,
        warmup_ticks=1,
        sample_ticks=1
    )
    # We need a way to check if replay was disabled in the kernel
    # For now, we'll check the output schema if it includes replay_enabled flag
    assert "replay_enabled" in result
    assert result["replay_enabled"] is False

def test_benchmark_disables_frame_pacing_by_default(base_state, profile):
    """
    Law:
        Perf TPS must measure compute throughput, not artificial sleep pacing.
    """
    from src.perf.profiles import make_perf_profile
    # Create a profile with high budget to test pacing
    pacing_profile = make_perf_profile("PACING_TEST", ram_mb=512, workers=0, tick_budget_ms=100.0)
    
    harness = BenchHarness(pacing_profile)
    
    start = time.perf_counter()
    result = harness.run_benchmark(
        scenario_id="TEST",
        initial_state=base_state,
        warmup_ticks=0,
        sample_ticks=5
    )
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    
    # If frame pacing was ON, it would take at least 500ms
    # With it OFF, it should be much faster
    assert result["frame_pacing_enabled"] is False
    assert elapsed_ms < 100.0 # Should be very fast

def test_recorded_tick_compute_includes_all_phases(base_state, profile):
    """
    Law:
        RuntimeStatus tick_compute_ms must include all authoritative tick phases.
    """
    rng = DeterministicRNG(42)
    # We'll check the kernel directly
    kernel = Kernel(profile, base_state, rng)
    try:
        kernel.tick_once()

        history = kernel.status.get_recent_history(1)
        tick_compute = history[0].tick_compute_ms
        phase_sum = sum(history[0].phase_costs_ms.values())

        # tick_compute should be very close to the sum of phases
        assert tick_compute >= phase_sum
        # And it should include 'persistence'
        assert "persistence" in history[0].phase_costs_ms
    finally:
        kernel.shutdown()

def test_benchmark_schema_contains_compute_and_wall_clock_metrics(base_state, profile):
    """
    Law:
        Benchmark report must distinguish compute-only cost from wall-clock elapsed time.
    """
    harness = BenchHarness(profile)
    result = harness.run_benchmark(
        scenario_id="TEST",
        initial_state=base_state,
        warmup_ticks=1,
        sample_ticks=10
    )
    
    assert "avg_tick_compute_ms" in result
    assert "compute_tps" in result
    assert "wall_clock_tps" in result
    assert "wall_clock_s" in result
    assert result["compute_tps"] >= result["wall_clock_tps"]
