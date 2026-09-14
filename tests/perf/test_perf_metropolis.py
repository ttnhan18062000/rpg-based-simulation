import pytest
from dataclasses import replace
from src.perf.scenarios import build_metropolis_state
from tests.tools.perf_assertions import assert_perf_threshold

@pytest.mark.perf
@pytest.mark.extra_slow
@pytest.mark.resource_budget_large
def test_perf_metropolis_stress(perf_harness, request):
    """
    Stress test: 1000 entities in a complex Metropolis environment.
    Goal: Verify O(N) scaling for governance and spatial lookups.

    Re-tiered to extra_slow/resource_budget_large (TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER,
    2026-09-14): this is a 1000-entity, 55-tick (5 warmup + 50 sample) benchmark that already ran
    23s under the "medium" 60s budget with ENABLE_COMBAT_ENGAGEMENT OFF -- a slow test that was
    carrying a medium marker regardless of that flag. Turning the flag ON pushed it over the 60s
    wall clock (TimeoutError), which is what surfaced the mis-tiering, but the re-tier is justified
    on its own terms: a benchmark already consuming over a third of its budget before this ticket
    touched anything was never really a "medium" test. The user reviewed the alternative (reduce
    this ticket's own ~198ms/tick contribution -- only ~18% of the real delta) and chose this
    re-tier instead, with the real numbers in hand: enabling the flag makes real combat volume rise
    4.1x (72->297 combat events over 20 ticks), and 82% of the resulting per-tick cost increase is
    the REST of the engine doing more work because the world now behaves differently (advancement's
    apply/hard-law-check/observability costs, cooperation, resolution_overhead) -- not this
    ticket's own combat_engagement phase. Full attribution table and the confirmed soft-gate
    instance (both thresholds below already breach with the flag OFF and still report green,
    since assert_perf_threshold() defaults hard=False) are recorded in
    docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md's
    own "Confirmed field evidence, 2026-09-14" note -- an existing perf epic already tracks this
    gap and this ticket routed real evidence into it rather than opening a rival one.

    IMPORTANT: passing here after the re-tier means the wall clock now fits the extra_slow budget.
    It does NOT mean performance is acceptable -- both thresholds below already breach and
    assert_perf_threshold() defaults to a soft (warning-only) gate, so a breach has never failed
    this test and still doesn't. Read the actual reported numbers, not this test's own green/red.
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

    # Assertions -- left exactly as they were before the re-tier above (not touched, per the
    # gate-integrity rule: this is a tier change, not a fix, and both already breach today under
    # real combat volume -- see this test's own docstring).
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
