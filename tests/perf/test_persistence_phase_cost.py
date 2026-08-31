"""Persistence-phase cost regression guard (TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION).

Reproduces investigation.md's own "Clean (no-profiler) run" methodology — drive a real,
unmocked Kernel through urban_political/seed=42 with `no_frame_pacing=True`, reading
`Kernel._phase_costs["persistence"]` after every `tick_once()` — and asserts the
`persistence`-phase share of total tick cost stays within a soft-monitor ceiling.

Real before/after numbers measured for this ticket (500-tick clean runs, same
world/seed/harness):

  pre-fix (investigation.md):  mean=8.891ms sum=4445.7ms  29.3% share  max=243.150ms
  post-fix (this ticket):      mean=8.817ms sum=4408.6ms  30.3% share  max=83.507ms

The `persistence` phase's steady-state cost is dominated by `CanonicalStateHasher.get_hash()`
(every tick in NORMAL/CONSTRAINED mode, INFRA-223, deliberately not touched by this ticket —
see the ticket's Implementation Notes), so Steps 1-3's fixes do not move the mean/sum
much. What they do eliminate is the ~100-tick-periodic redundant-serialization spikes
Root cause #1 caused (max persistence-phase tick cost dropped from 243ms to 83ms in the
500-tick comparison above) and the per-record flush overhead (Root cause #2) that was the
actual `CalibrationIntegrityError` driver in the separate `QualityPersistence`/
`EventRecorder` telemetry pipeline — a different code path from this tick-phase, not
reflected in `_phase_costs["persistence"]` at all.

A real 1000-tick measurement for this ticket's post-fix code (same methodology) gave a
23.3% persistence-phase share of total tick cost — the ceiling below is that measured
number plus 10 percentage points of headroom, per this ticket's plan.md Step 7.
"""
from __future__ import annotations

import pytest

from tests.tools.perf_assertions import assert_perf_threshold

SEED = 42
WORLD_NAME = "urban_political"
TICKS = 1000

# Measured post-fix (this ticket): 23.3% persistence-phase share of total tick cost over
# a 1000-tick clean run. +10 percentage points of headroom to absorb CI hardware variance,
# per plan.md Step 7.
PERSISTENCE_SHARE_CEILING_PCT = 33.3


def _run_clean_kernel_and_measure_persistence_share() -> tuple[float, float]:
    """Drive a real Kernel for TICKS ticks; return (persistence_share_pct, max_persistence_ms)."""
    import tools.calibrate_simq as cal_mod
    from src.config.profiles import PROD_SMALL
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG

    state, _report = cal_mod._load_world_state(WORLD_NAME, SEED)
    assert state is not None, f"{WORLD_NAME!r} must resolve to a real compiled world"

    rng = DeterministicRNG(SEED)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=rng, flags={"no_frame_pacing": True})

    persistence_costs = []
    total_costs = []
    try:
        for _ in range(TICKS):
            kernel.tick_once()
            persistence_costs.append(kernel._phase_costs.get("persistence", 0.0))
            total_costs.append(sum(kernel._phase_costs.values()))
    finally:
        kernel.shutdown()

    persistence_sum = sum(persistence_costs)
    total_sum = sum(total_costs)
    share_pct = (persistence_sum / total_sum * 100.0) if total_sum > 0 else 0.0
    return share_pct, max(persistence_costs)


@pytest.mark.slow
def test_persistence_phase_cost_regression_guard_1000t():
    """Soft-monitor (warn, never fail) guard on persistence-phase share of total tick cost
    for a representative 1000-tick urban_political/seed=42 run — see this file's module
    docstring for the measured pre-/post-fix numbers this ceiling is derived from."""
    share_pct, max_persistence_ms = _run_clean_kernel_and_measure_persistence_share()

    print(
        f"\npersistence-phase share of total tick cost over {TICKS} ticks: "
        f"{share_pct:.1f}% (ceiling: {PERSISTENCE_SHARE_CEILING_PCT}%), "
        f"max single-tick persistence cost: {max_persistence_ms:.1f}ms"
    )
    assert_perf_threshold(
        share_pct, PERSISTENCE_SHARE_CEILING_PCT,
        "persistence-phase share of total tick cost for a 1000-tick urban_political/seed=42 "
        "run (ceiling = this ticket's measured post-fix 23.3% + 10 percentage points headroom, "
        "see docstring)", op="<",
    )
