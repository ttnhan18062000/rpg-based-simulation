import pytest
from src.perf.scenarios import build_mixed_state

@pytest.mark.perf
@pytest.mark.slow
def test_perf_mixed_stress(perf_harness, request):
    """
    Stress test: 200 entities with mixed work (Heroes, Monsters, Resource Nodes).
    Goal: Verify performance under realistic load.
    """
    harness = perf_harness("PERF_1GB_LOCAL")
    state = build_mixed_state(entity_count=200)
    
    results = harness.run_benchmark(
        scenario_id="MIXED_200",
        initial_state=state,
        warmup_ticks=100,
        sample_ticks=1000
    )
    
    # Store for reporter
    request.node.perf_results = results
    
    # Assertions
    # 200 mixed entities is very heavy for this environment.
    assert results["avg_tps"] > 5.0
    assert results["mem_rss_mb"]["max"] < 1024.0
    # Hard cap at 200ms for p99
    assert results["tick_ms"]["p99"] < 200.0
