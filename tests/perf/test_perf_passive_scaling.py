import pytest
from src.perf.scenarios import build_idle_state

@pytest.mark.perf
@pytest.mark.slow
@pytest.mark.parametrize("count", [100, 1000, 5000])
def test_perf_passive_scaling(perf_harness, request, count):
    """
    Test passive overhead scaling (apply_passive + to_readonly).
    Goal: Quantify impact of passive update staggering.
    """
    harness = perf_harness("PERF_512MB_LOCAL")
    state = build_idle_state(entity_count=count)
    
    results = harness.run_benchmark(
        scenario_id=f"PASSIVE_SCALING_{count}",
        initial_state=state,
        warmup_ticks=20,
        sample_ticks=100,
        flags={"no_replay": True}
    )
    
    request.node.perf_results = results
    
    # Report metrics
    print(f"\nScaling Test [{count} entities]:")
    print(f"  Avg TPS: {results['avg_tps']:.2f}")
    print(f"  p95 Tick: {results['tick_ms']['p95']:.2f}ms")
    print(f"  Max RSS: {results['mem_rss_mb']['max']:.1f}MB")
    
    p95_ms = results['tick_ms']['p95']
    max_rss = results['mem_rss_mb']['max']
    mem_delta = results['mem_rss_mb']['delta']
    
    # Automated Assertions
    if count == 100:
        assert p95_ms < 25.0, f"Expected p95 latency < 25ms, got {p95_ms:.2f}ms"
    elif count == 1000:
        assert p95_ms < 175.0, f"Expected p95 latency < 175ms, got {p95_ms:.2f}ms"
    elif count == 5000:
        assert p95_ms < 450.0, f"Expected p95 latency < 450ms, got {p95_ms:.2f}ms"
        
    expected_max_rss = 450.0 + (count / 1000.0) * 30.0
    assert max_rss < expected_max_rss, f"RSS {max_rss:.1f}MB exceeded suite limit of {expected_max_rss:.1f}MB for {count} entities"
    allowed_delta = 50.0 if count >= 5000 else 25.0
    assert mem_delta < allowed_delta, f"Memory leak detected during simulation ticks: delta {mem_delta:.1f}MB >= {allowed_delta}MB"
