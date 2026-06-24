import pytest
from src.perf.scenarios import build_idle_state

@pytest.mark.perf
@pytest.mark.slow
def test_perf_idle_baseline(perf_harness, request):
    """
    Baseline test: 100 entities in idle state.
    Goal: Verify minimal engine overhead.
    """
    harness = perf_harness("PERF_512MB_LOCAL")
    state = build_idle_state(entity_count=100)
    
    results = harness.run_benchmark(
        scenario_id="IDLE_100",
        initial_state=state,
        warmup_ticks=50,
        sample_ticks=500
    )
    
    # Store for reporter
    request.node.perf_results = results
    
    # Assertions
    # Baseline: 100 idle entities should exceed 20 TPS on this environment.
    assert results["avg_tps"] > 20.0
    assert results["mem_rss_mb"]["max"] < 512.0
    # p99 might spike due to GC or other noise, set to 100ms
    assert results["tick_ms"]["p99"] < 100.0
