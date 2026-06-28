"""
5,000-tick behavioral regression harness.

Ticket: TCK-20260628-E-LONGRUN-REGRESSION
Baseline: tests/regression/baseline_5k.json  (seed=42, urban_political, routing=ON)

Catches behavioral regressions in entity survival, economic activation, and
quest activity across long simulation runs.

Run:              pytest tests/regression/ -m extra_slow
Refresh baseline: make regression-baseline
"""
from __future__ import annotations

import json
import pytest
from dataclasses import replace
from pathlib import Path
from typing import Any

SEED = 42
WORLD_ID = "urban_political"
TICKS = 5000
SAMPLE_INTERVAL = 100  # sample every N ticks → 50 samples over 5k-tick run

BASELINE_PATH = Path("tests/regression/baseline_5k.json")

# Allowed relative deviation from baseline before test fails.
# Bands chosen empirically from D06 1k-tick variance (ticket §Assumptions).
THRESHOLDS: dict[str, float] = {
    "alive_avg":          0.10,   # ±10%
    "gold_avg":           0.20,   # ±20%
    "quest_active_count": 0.20,   # ±20%
}


# ── Harness ───────────────────────────────────────────────────────────────────

def collect_behavioral_metrics(
    ticks: int = TICKS,
    seed: int = SEED,
    world_id: str = WORLD_ID,
) -> dict[str, Any]:
    """
    Run `ticks`-tick simulation and return summary behavioral metrics.

    Adventure routing is explicitly enabled so the pipeline exercises
    non-survival goal selection — the domain that most behavioral regressions
    affect.
    """
    from src.worldbuilding.repository import WorldRepository
    from src.worldbuilding.compiler import WorldCompiler
    from src.engine.kernel import Kernel
    from src.engine.metrics import MetricsService
    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.platform.rng import DeterministicRNG

    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)
    state, _ = WorldCompiler.compile(spec, seed=seed)

    # Enable adventure routing — required for economic and quest metrics to activate.
    flags = dict(state.feature_flags)
    flags["ENABLE_ADVENTURE_ROUTING"] = 1.0
    state = replace(state, feature_flags=flags)

    profile = RuntimeProfile(
        name="behavioral-regression-5k",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=2048,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=2000,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=500.0,
    )
    # no_frame_pacing disables the kernel's tick-rate sleep (which pads each tick to
    # max_tick_budget_ms). Without this flag, 5000 ticks × 500ms = ~45 minutes.
    kernel = Kernel(profile=profile, state=state, rng=DeterministicRNG(seed),
                    flags={"no_frame_pacing": True})

    samples: list[dict[str, Any]] = []
    try:
        for tick in range(1, ticks + 1):
            kernel.tick_once()
            if tick % SAMPLE_INTERVAL == 0:
                m = MetricsService.extract_metrics(kernel.state)
                samples.append({
                    "tick": tick,
                    "alive": m.alive_entities,
                    "gold": m.total_gold,
                    "quest_active": m.quest_status_counts.get("ACTIVE", 0),
                })
    finally:
        kernel.shutdown()

    n = max(len(samples), 1)
    return {
        "ticks": ticks,
        "seed": seed,
        "world_id": world_id,
        "sample_interval": SAMPLE_INTERVAL,
        "sample_count": n,
        "alive_avg":          round(sum(s["alive"]        for s in samples) / n, 4),
        "gold_avg":           round(sum(s["gold"]         for s in samples) / n, 4),
        "quest_active_count": round(sum(s["quest_active"] for s in samples) / n, 4),
    }


# ── Comparison ────────────────────────────────────────────────────────────────

def _check_metric(
    name: str, actual: float, baseline: float, threshold: float
) -> list[str]:
    """Return a list of failure strings (empty ↔ pass)."""
    if baseline == 0.0:
        # Absolute tolerance when baseline is zero
        tol = threshold
        delta = abs(actual - baseline)
        if delta > tol:
            return [
                f"{name}: actual={actual:.4f} baseline=0 "
                f"(absolute delta {delta:.4f} > {tol:.4f})"
            ]
        return []
    drift = abs(actual - baseline) / baseline
    if drift > threshold:
        return [
            f"{name}: actual={actual:.4f} baseline={baseline:.4f} "
            f"drift={drift:.1%} > allowed={threshold:.0%}"
        ]
    return []


# ── Test ──────────────────────────────────────────────────────────────────────

@pytest.mark.extra_slow
@pytest.mark.regression
def test_behavioral_5k_regression():
    """
    Run 5,000 ticks (seed=42, urban_political) and assert that key behavioral
    metrics stay within threshold bands of the committed baseline.

    Catches:
    - Survival-rate regressions (alive_avg ±10%)
    - Economic activation regressions (gold_avg ±20%)
    - Quest-system regressions (quest_active_count ±20%)

    If the baseline is intentionally outdated (e.g., after a deliberate design
    change), refresh it with `make regression-baseline` and commit the result.
    """
    if not BASELINE_PATH.exists():
        pytest.skip(
            f"Baseline not found at {BASELINE_PATH}. "
            "Run `make regression-baseline` to generate it, then commit the file."
        )

    baseline = json.loads(BASELINE_PATH.read_text())
    baseline_metrics: dict[str, float] = baseline["metrics"]

    actual = collect_behavioral_metrics()

    failures: list[str] = []
    for metric, threshold in THRESHOLDS.items():
        failures.extend(
            _check_metric(
                metric,
                actual.get(metric, 0.0),
                baseline_metrics.get(metric, 0.0),
                threshold,
            )
        )

    assert not failures, (
        f"Behavioral regression detected — {len(failures)} metric(s) out of band "
        f"(seed={SEED}, world={WORLD_ID}, ticks={TICKS}):\n"
        + "\n".join(f"  • {f}" for f in failures)
        + "\n\nTo accept the new behavior: `make regression-baseline` then commit."
    )
