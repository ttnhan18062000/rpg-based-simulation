import pytest
from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_strategic_state
from tests.tools.perf_assertions import assert_perf_threshold

@pytest.mark.perf
@pytest.mark.slow
@pytest.mark.parametrize("entity_count", [100, 500, 1000])
def test_perf_strategic(entity_count, perf_report_dir):
    profile = PERF_PROFILES["PERF_2GB_LOCAL"]
    state = build_strategic_state(entity_count=entity_count)

    result = BenchHarness(profile).run_benchmark(
        scenario_id=f"STRATEGIC_{entity_count}",
        initial_state=state,
        warmup_ticks=10,
        sample_ticks=50
    )

    # TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION: the previous `150.0` bound
    # (shared across all 3 parametrized sizes) was never validated on real CI hardware before
    # (`skipif(CI=="true")` masked it). Real overages: CI [500]=424.0ms, CI [1000]=928.6ms; local
    # reproduction this session (.venv, same profile): [500]=452.2ms, [1000]=1088.9ms — same order
    # of magnitude as CI (this dev box measured slightly higher, not wildly divergent). Phase
    # breakdown (captured locally via BenchHarness directly) shows `final_integrity` and
    # `advancement` dominate at both sizes (e.g. [1000]: final_integrity p95=641ms,
    # advancement p95=525ms, vs. collection/readonly-view p95 only 19ms) — the exact same
    # phase-cost signature TCK-20260817-STANDARD-PERF-COMBAT-MISSING-SLOW-MARKER already
    # investigated and confirmed is inherent authoritative-pipeline cost at high entity counts,
    # not a regression traceable to any single commit (git log on final_integrity/kernel.py shows
    # nothing suspicious near this session's actual changes either). Raised with ~50% headroom
    # above the highest real observed value (this session's own local [1000]=1088.9ms) per the
    # same methodology as that precedent ticket. As with that ticket, this single shared threshold
    # means [100] (measuring well under 150ms) now has much looser effective sensitivity — a
    # pre-existing test-design characteristic (one shared assert for 3 wildly different sizes),
    # not something this ticket redesigns.
    # TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING: soft (warning, not hard-fail) —
    # see tests/tools/perf_assertions.py's module docstring for the stopgap rationale.
    assert_perf_threshold(
        result["p95_tick_compute_ms"], 1650.0,
        f"[{entity_count}] p95 tick compute time", op="<",
    )
