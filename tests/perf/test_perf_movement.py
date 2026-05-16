import pytest
from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_movement_state

@pytest.mark.perf
@pytest.mark.parametrize("entity_count", [100, 500, 1000, 5000])
def test_perf_movement(entity_count, perf_report_dir):
    profile = PERF_PROFILES["PERF_2GB_LOCAL"]
    state = build_movement_state(entity_count=entity_count)
    
    result = BenchHarness(profile).run_benchmark(
        scenario_id=f"MOVEMENT_{entity_count}",
        initial_state=state,
        warmup_ticks=10,
        sample_ticks=50
    )
    
    threshold = 1000.0 if entity_count >= 5000 else (250.0 if entity_count >= 1000 else (125.0 if entity_count >= 500 else 50.0))
    print(f"\n[{entity_count}] p95={result['p95_tick_compute_ms']:.2f}ms. BREAKDOWN:", result["phase_breakdown"])
    assert result["p95_tick_compute_ms"] < threshold
