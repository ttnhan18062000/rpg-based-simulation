import pytest
from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_resource_state

@pytest.mark.perf
@pytest.mark.parametrize("entity_count,node_count", [(100, 100), (500, 500), (1000, 1000)])
def test_perf_resource(entity_count, node_count, perf_report_dir):
    profile = PERF_PROFILES["PERF_2GB_LOCAL"]
    state = build_resource_state(entity_count=entity_count, node_count=node_count)
    
    result = BenchHarness(profile).run_benchmark(
        scenario_id=f"RESOURCE_{entity_count}_N{node_count}",
        initial_state=state,
        warmup_ticks=10,
        sample_ticks=50
    )
    
    assert result["p95_tick_compute_ms"] < 150.0
