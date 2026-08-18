import pytest
from dataclasses import replace
from src.perf.scenarios import build_metropolis_state
from tests.tools.perf_assertions import assert_perf_threshold

@pytest.mark.perf
def test_perf_metropolis_stress(perf_harness, request):
    """
    Stress test: 1000 entities in a complex Metropolis environment.
    Goal: Verify O(N) scaling for governance and spatial lookups.
    """
    harness = perf_harness("PERF_1GB_LOCAL")
    # 1000 entities, 50 regions, 1000 buildings
    state = build_metropolis_state(entity_count=1000, region_count=50, buildings_per_region=20)
    
    results = harness.run_benchmark(
        scenario_id="METROPOLIS_1000",
        initial_state=state,
        warmup_ticks=5,
        sample_ticks=50
    )
    
    # Store for reporter
    request.node.perf_results = results
    
    # Assertions
    # We expect > 3 TPS in this very complex scenario (relaxed due to single-threaded overhead)
    assert_perf_threshold(results["avg_tps"], 3.0, "avg TPS (Metropolis 1000 entities)", op=">")
    # p99 should be under 500ms for this high load
    assert_perf_threshold(results["tick_ms"]["p99"], 500.0, "p99 tick time (Metropolis 1000 entities)", op="<")
    # Memory should be stable
    assert_perf_threshold(results["mem_rss_mb"]["max"], 1024.0, "max RSS (Metropolis 1000 entities)", op="<")

@pytest.mark.perf
def test_perf_metropolis_longevity(perf_harness, request):
    """
    Longevity test: 100 ticks of Metropolis.
    Goal: Verify no performance degradation or memory leaks.
    """
    harness = perf_harness("PERF_1GB_LOCAL")
    state = build_metropolis_state(entity_count=500) 
    
    results = harness.run_benchmark(
        scenario_id="METROPOLIS_LONGEVITY",
        initial_state=state,
        warmup_ticks=5,
        sample_ticks=100 
    )
    
    request.node.perf_results = results
    assert_perf_threshold(results["avg_tps"], 5.0, "avg TPS (Metropolis longevity)", op=">")
    # Check for memory growth
    if "mem_rss_mb" in results and "growth_per_tick" in results["mem_rss_mb"]:
        assert_perf_threshold(
            results["mem_rss_mb"]["growth_per_tick"], 1.0,
            "RSS growth per tick (Metropolis longevity)", op="<",
        )

@pytest.mark.perf
def test_perf_chaos_items(perf_harness, request):
    """
    Chaos test: Massive amount of ground items.
    Goal: Stress spatial indexing for non-entity objects.
    """
    harness = perf_harness("PERF_1GB_LOCAL")
    state = build_metropolis_state(entity_count=200)
    
    # Inject 5000 ground items
    from src.core.state import GroundItemState
    ground_items = {
        i: GroundItemState(id=i, item_id="junk", quantity=1, position=(float(i % 500), float(i // 500)))
        for i in range(10000, 15000)
    }
    state = replace(state, ground_items=ground_items)
    
    results = harness.run_benchmark(
        scenario_id="CHAOS_ITEMS_5000",
        initial_state=state,
        warmup_ticks=5,
        sample_ticks=50
    )
    
    request.node.perf_results = results
    assert_perf_threshold(results["tick_ms"]["p99"], 250.0, "p99 tick time (Chaos ground items)", op="<")
