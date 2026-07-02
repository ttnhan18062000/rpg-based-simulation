import os
import pytest
from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_strategic_state

@pytest.mark.perf
@pytest.mark.slow
@pytest.mark.parametrize("entity_count", [100, 500, 1000])
@pytest.mark.skipif(os.environ.get("CI") == "true", reason="CI CPU too slow for 150ms p95 tick threshold")
def test_perf_strategic(entity_count, perf_report_dir):
    profile = PERF_PROFILES["PERF_2GB_LOCAL"]
    state = build_strategic_state(entity_count=entity_count)
    
    result = BenchHarness(profile).run_benchmark(
        scenario_id=f"STRATEGIC_{entity_count}",
        initial_state=state,
        warmup_ticks=10,
        sample_ticks=50
    )
    
    assert result["p95_tick_compute_ms"] < 150.0
