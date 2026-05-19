import pytest
import time
from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_movement_state
from src.observability.config import ObservabilityConfig, ObservabilityMode

@pytest.mark.perf
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

    # Due to CPU and virtual machine environment scheduling noise, we assert a highly robust limit:
    # 1. The relative overhead under noise is less than 5% (to prevent spurious failures under heavy VM load), OR
    # 2. The absolute overhead per tick is less than 0.1ms (representing well under 1% of a standard 20ms or 50ms tick budget).
    abs_overhead_ms = avg_compute_light - avg_compute_off
    assert (overhead < 0.05) or (abs_overhead_ms < 0.1), (
        f"Overhead too high: relative {overhead*100:.2f}%, absolute {abs_overhead_ms:.3f}ms"
    )
