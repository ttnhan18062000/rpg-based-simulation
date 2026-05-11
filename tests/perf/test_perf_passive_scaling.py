import pytest
from src.perf.scenarios import build_idle_state

@pytest.mark.perf
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
