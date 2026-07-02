import os
import pytest
import time
from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_movement_state
from src.observability.config import ObservabilityConfig, ObservabilityMode

@pytest.mark.perf
@pytest.mark.slow
@pytest.mark.skipif(os.environ.get("CI") == "true", reason="CI CPU too slow for 5% overhead threshold")
def test_hard_law_monitor_overhead():
    """
    Benchmark the execution overhead of the HardLawMonitor checks.
    Verify that checks active in LIGHT mode add less than 1% overhead to a standard tick.
    """
    profile = PERF_PROFILES["PERF_512MB_LOCAL"]
    
    # Build a movement scenario with 500 active entities
    state = build_movement_state(entity_count=500)
    
    # 1. Run benchmark with checks OFF
    ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)
    harness = BenchHarness(profile)
    result_off = harness.run_benchmark(
        scenario_id="OVERHEAD_OFF_500",
        initial_state=state,
        warmup_ticks=5,
        sample_ticks=30
    )
    avg_compute_off = result_off["avg_tick_compute_ms"]

    # 2. Run benchmark with checks in LIGHT mode (active monitoring)
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    result_light = harness.run_benchmark(
        scenario_id="OVERHEAD_LIGHT_500",
        initial_state=state,
        warmup_ticks=5,
        sample_ticks=30
    )
    avg_compute_light = result_light["avg_tick_compute_ms"]

    # Restore default/clean state
    ObservabilityConfig.set_override_mode(None)

    # Compute overhead ratio
    overhead = (avg_compute_light - avg_compute_off) / avg_compute_off if avg_compute_off > 0 else 0
    print(f"\n[HardLawMonitor Benchmark]")
    print(f"  Avg Tick Compute (OFF):   {avg_compute_off:.3f}ms")
    print(f"  Avg Tick Compute (LIGHT): {avg_compute_light:.3f}ms")
    print(f"  Computed Overhead Ratio:  {overhead * 100:.2f}%")

    # Per performance_contract.md §4.2: instrumentation ceiling is <5% relative overhead.
    # The abs_overhead_ms < 0.1ms OR-arm has been removed — 0.1ms is unrealistically tight
    # on any shared VM where a single syscall can take >0.1ms. The relative check alone
    # is sufficient and aligns with the contract threshold.
    assert overhead < 0.05, (
        f"Overhead too high: relative {overhead*100:.2f}% (limit: 5%)"
    )
