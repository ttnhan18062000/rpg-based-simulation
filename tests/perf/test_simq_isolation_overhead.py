"""Three-mode SimQ engine-overhead benchmark (TCK-20260702-OBSISO-ISOLATION-PROOF, G5).

Measures engine tick throughput and engine-process CPU time under three SimQ
configs on the `sandbox_world` seed-42 scenario, driven through
src.perf.bench_harness.BenchHarness (warmup=100, sample=1000, per
docs/performance/perf_baseline_policy.md Section 2.1's minimums):

  (a) QUALITY_SCORING_DISABLED=1 -- EventRecorder stays fully enabled (JSONL/
      stream/queue running); only the quality_fn callback is skipped. This is
      NOT ObservabilityMode.OFF -- do not compare these numbers against
      tests/perf/test_production_observatory_overhead.py's OFF-vs-LIGHT figures.
  (b) QUALITY_FEED_MODE=inprocess (default) -- QualityHub built in-engine.
  (c) QUALITY_FEED_MODE=broker -- QualityHub runs in a separate QualityWorker
      subprocess; requires a running Redis instance. Provision manually before
      running this file's broker-dependent tests:

          docker run -d --name simq-isolation-proof-redis -p 6379:6379 redis:7-alpine
          REDIS_AVAILABLE=1 pytest tests/perf/test_simq_isolation_overhead.py -m slow
          docker rm -f simq-isolation-proof-redis

      Without a reachable Redis, the broker leg and its regression-guard test
      skip (never fail) -- this benchmark's other two legs still run.

OBS_DECISION_TRACE is held constant ("1") across all three runs so
DecisionTraceWriter's independent QueueDrainWorker thread cannot become an
uncontrolled confound in the comparison (see investigation.md's Anti-Drift
Hazards).

Results and the locked regression-guard thresholds are documented in
docs/performance/simq_isolation_overhead.md -- this file is the source of the
numbers recorded there, not a duplicate of them.

Also includes a standing regression gate (TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE)
for the apply-layer push-shaper registry's (`src/observability/event_shapers.py`)
cumulative CPU cost, measured as `ENABLE_PUSH_EVENT_SHAPERS=ON` vs `OFF` under the
`inprocess` SimQ mode (the live default) -- orthogonal to the three SimQ-delivery
modes above, which never vary this flag. See
docs/performance/simq_isolation_overhead.md's "Push-Shaper Registry Overhead"
section for the committed numbers this test's output feeds.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, replace as dc_replace
from pathlib import Path
from typing import Optional

import pytest

from src.perf.bench_harness import BenchHarness
from src.config.profiles import PROD_SMALL
from tests.tools.perf_assertions import assert_perf_threshold

REPO_ROOT = Path(__file__).resolve().parents[2]

SEED = 42
WORLD_NAME = "sandbox_world"
WARMUP_TICKS = 100
SAMPLE_TICKS = 1000
WORKER_READY_TIMEOUT_S = 10.0
WORKER_PORT = 18091


def _redis_available() -> bool:
    try:
        import redis
        client = redis.Redis(host="localhost", port=6379, socket_connect_timeout=1)
        return bool(client.ping())
    except Exception:
        return False


REDIS_AVAILABLE = _redis_available()


@dataclass
class ModeResult:
    mode_label: str
    wall_clock_tps: float
    cpu_time_total_delta_s: float
    obs_decision_trace: str


def _build_state():
    import tools.calibrate_simq as cal_mod

    state, _report = cal_mod._load_world_state(WORLD_NAME, SEED)
    assert state is not None, f"{WORLD_NAME!r} must resolve to a real compiled state, got None"
    return state


def _clear_quality_env(monkeypatch) -> None:
    for var in (
        "QUALITY_SCORING_DISABLED", "QUALITY_FEED_MODE", "QUALITY_BROKER_URL",
        "QUALITY_STREAM_NAME", "QUALITY_CONSUMER_GROUP", "QUALITY_RUN_ID",
        "QUALITY_RUN_DIR", "SIM_STREAM_BACKEND", "RPG_STREAM_BACKEND",
    ):
        monkeypatch.delenv(var, raising=False)
    # Held constant across all three modes so TRACE-ASYNC's independent
    # QueueDrainWorker thread cannot become an uncontrolled confound.
    monkeypatch.setenv("OBS_DECISION_TRACE", "1")


def _assert_mode_a_is_not_observability_off(monkeypatch, tmp_path) -> None:
    """Encodes Key Decision #1 as a running check, not just doc prose:
    QUALITY_SCORING_DISABLED=1 must leave EventRecorder fully enabled (JSONL
    still writing) -- it must never be conflated with ObservabilityMode.OFF."""
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG

    _clear_quality_env(monkeypatch)
    monkeypatch.setenv("QUALITY_SCORING_DISABLED", "1")

    state = _build_state()
    rng = DeterministicRNG(state.seed)
    kernel = Kernel(PROD_SMALL, state, rng, flags={"no_replay": True, "no_frame_pacing": True})
    try:
        assert kernel.event_recorder.enabled is True, (
            "QUALITY_SCORING_DISABLED=1 must not disable EventRecorder itself -- "
            "that would silently conflate mode (a) with ObservabilityMode.OFF"
        )
        assert kernel._quality_hub is None, "mode (a) must build zero in-engine QualityHub"
        for _ in range(10):
            kernel.tick_once()
        jsonl_path = kernel.event_recorder.filepath
        assert jsonl_path is not None and os.path.exists(jsonl_path), (
            "mode (a) must still be writing simulation_events.jsonl -- EventRecorder "
            "is fully enabled, only the quality_fn callback is skipped"
        )
    finally:
        kernel.shutdown()


def _run_mode_disabled(monkeypatch) -> ModeResult:
    _clear_quality_env(monkeypatch)
    monkeypatch.setenv("QUALITY_SCORING_DISABLED", "1")
    result = BenchHarness(PROD_SMALL).run_benchmark(
        scenario_id=f"{WORLD_NAME}_seed{SEED}_disabled",
        initial_state=_build_state(),
        warmup_ticks=WARMUP_TICKS,
        sample_ticks=SAMPLE_TICKS,
        flags={"no_replay": True, "no_frame_pacing": True},
    )
    return ModeResult("disabled", result["wall_clock_tps"], result["cpu_time_total_delta_s"], "1")


def _run_mode_inprocess(monkeypatch) -> ModeResult:
    _clear_quality_env(monkeypatch)
    monkeypatch.setenv("QUALITY_FEED_MODE", "inprocess")
    result = BenchHarness(PROD_SMALL).run_benchmark(
        scenario_id=f"{WORLD_NAME}_seed{SEED}_inprocess",
        initial_state=_build_state(),
        warmup_ticks=WARMUP_TICKS,
        sample_ticks=SAMPLE_TICKS,
        flags={"no_replay": True, "no_frame_pacing": True},
    )
    return ModeResult("inprocess", result["wall_clock_tps"], result["cpu_time_total_delta_s"], "1")


def _run_mode_inprocess_with_shaper_flag(monkeypatch, shapers_on: bool) -> ModeResult:
    """Same `inprocess` SimQ config as `_run_mode_inprocess`, but with
    `AuthoritativeState.feature_flags["ENABLE_PUSH_EVENT_SHAPERS"]` pinned
    explicitly, rather than left at its default (`"ON"` when absent, per
    `kernel.py`'s `_phase_observability`). Orthogonal to `QUALITY_FEED_MODE`
    -- this varies which observability *emission* path (apply-layer shaper
    registry vs. post-tick diffing extractor) produces COMBAT/ECONOMY/FACTION
    events in the first place, not how SimQ scores them once emitted."""
    _clear_quality_env(monkeypatch)
    monkeypatch.setenv("QUALITY_FEED_MODE", "inprocess")
    state = _build_state()
    state = dc_replace(state, feature_flags={
        **(state.feature_flags or {}),
        "ENABLE_PUSH_EVENT_SHAPERS": "ON" if shapers_on else "OFF",
    })
    result = BenchHarness(PROD_SMALL).run_benchmark(
        scenario_id=f"{WORLD_NAME}_seed{SEED}_shapers_{'on' if shapers_on else 'off'}",
        initial_state=state,
        warmup_ticks=WARMUP_TICKS,
        sample_ticks=SAMPLE_TICKS,
        flags={"no_replay": True, "no_frame_pacing": True},
    )
    label = "shapers_on" if shapers_on else "shapers_off"
    return ModeResult(label, result["wall_clock_tps"], result["cpu_time_total_delta_s"], "1")


def _run_mode_inprocess_with_phase2_flag(monkeypatch, phase2_on: bool) -> ModeResult:
    """Same shape as `_run_mode_inprocess_with_shaper_flag`, but varies
    `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` (the complete Phase 2 registry --
    StrategyShaper/ProgressionShaper/WorldDynamicsShaper/SocialShaper/
    DeferredInstrumentationShaper -- all 5 shapers together) instead of Phase
    1's single already-cutover flag. ENABLE_PUSH_EVENT_SHAPERS itself is left
    at its own default ("ON") in both legs, since Phase 1's own cost is
    already covered by the tests above -- this isolates Phase 2's own
    incremental cost specifically, per TCK-20260806-PUSH-SHADOW-VALIDATION-
    PERF-PHASE2's "full-registry" requirement."""
    _clear_quality_env(monkeypatch)
    monkeypatch.setenv("QUALITY_FEED_MODE", "inprocess")
    state = _build_state()
    state = dc_replace(state, feature_flags={
        **(state.feature_flags or {}),
        "ENABLE_PUSH_EVENT_SHAPERS_PHASE2": "ON" if phase2_on else "OFF",
    })
    result = BenchHarness(PROD_SMALL).run_benchmark(
        scenario_id=f"{WORLD_NAME}_seed{SEED}_phase2_{'on' if phase2_on else 'off'}",
        initial_state=state,
        warmup_ticks=WARMUP_TICKS,
        sample_ticks=SAMPLE_TICKS,
        flags={"no_replay": True, "no_frame_pacing": True},
    )
    label = "phase2_on" if phase2_on else "phase2_off"
    return ModeResult(label, result["wall_clock_tps"], result["cpu_time_total_delta_s"], "1")


def _wait_worker_ready(port: int, timeout_s: float = WORKER_READY_TIMEOUT_S) -> None:
    """Poll /health's pillar_event_counts (not current_tick, which is 0 at
    construction and would pass trivially) until it shows a real, live
    publish -> Redis -> consumer-thread -> hub.on_envelope round trip."""
    from src.observability.events import SimulationEvent
    from src.observability.stream.factory import get_event_stream_adapter

    # event_type/category chosen to match a real scorer's routing (AgencyScorer
    # scores action_executed/strategy, per test_worker.py's own
    # test_quality_worker_health_payload_includes_per_pillar_event_counts) --
    # an event category no scorer recognizes (e.g. "infrastructure") is
    # processed and XACKed without error but never moves pillar_event_counts,
    # which would make this readiness probe wait out its timeout every time.
    probe_event = SimulationEvent(
        event_type="action_executed",
        event_category="strategy",
        tick=0,
        severity="INFO",
        source_system="test_simq_isolation_overhead",
        message="broker worker readiness probe",
    )
    adapter = get_event_stream_adapter()
    adapter.publish(probe_event)
    adapter.flush()

    deadline = time.time() + timeout_s
    last_payload: Optional[dict] = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://localhost:{port}/health", timeout=1.0) as resp:
                payload = json.loads(resp.read())
                last_payload = payload
                counts = payload.get("pillar_event_counts") or {}
                if any(v > 0 for v in counts.values()):
                    return
        except (urllib.error.URLError, ConnectionError, OSError):
            pass
        time.sleep(0.25)

    raise AssertionError(
        f"QualityWorker on port {port} never reported non-zero pillar_event_counts within "
        f"{timeout_s}s (last /health payload: {last_payload}) -- broker-mode consumer never "
        "became ready"
    )


def _run_mode_broker(monkeypatch, tmp_path) -> Optional[ModeResult]:
    if not REDIS_AVAILABLE:
        return None

    _clear_quality_env(monkeypatch)
    monkeypatch.setenv("QUALITY_FEED_MODE", "broker")
    monkeypatch.setenv("SIM_STREAM_BACKEND", "redis")
    monkeypatch.setenv("QUALITY_BROKER_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("QUALITY_STREAM_NAME", "simulation:events")
    monkeypatch.setenv("QUALITY_CONSUMER_GROUP", "simq_isolation_proof_bench")

    from src.observability.stream.factory import reset_event_stream_adapter
    reset_event_stream_adapter()

    worker_run_dir = tmp_path / "broker_worker_run"
    env = dict(os.environ)
    env.update({
        "QUALITY_WORKER_PORT": str(WORKER_PORT),
        "QUALITY_RUN_ID": "simq-isolation-proof-worker",
        "QUALITY_RUN_DIR": str(worker_run_dir),
        "QUALITY_CONSUMER_GROUP": "simq_isolation_proof_bench",
        "QUALITY_BROKER_URL": "redis://localhost:6379/0",
        "QUALITY_STREAM_NAME": "simulation:events",
    })

    proc = subprocess.Popen(
        [sys.executable, "-m", "src.simulation_quality.worker"],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_worker_ready(WORKER_PORT)
        result = BenchHarness(PROD_SMALL).run_benchmark(
            scenario_id=f"{WORLD_NAME}_seed{SEED}_broker",
            initial_state=_build_state(),
            warmup_ticks=WARMUP_TICKS,
            sample_ticks=SAMPLE_TICKS,
            flags={"no_replay": True, "no_frame_pacing": True},
        )
        return ModeResult("broker", result["wall_clock_tps"], result["cpu_time_total_delta_s"], "1")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        reset_event_stream_adapter()


@pytest.mark.slow
def test_three_mode_engine_overhead_benchmark(monkeypatch, tmp_path):
    """AC #1: produces per-mode wall-clock TPS + engine CPU time for all three
    SimQ configs on sandbox_world/seed42. See docs/performance/simq_isolation_overhead.md
    for the committed results table this test's output feeds."""
    _assert_mode_a_is_not_observability_off(monkeypatch, tmp_path)

    disabled = _run_mode_disabled(monkeypatch)
    inprocess = _run_mode_inprocess(monkeypatch)
    broker = _run_mode_broker(monkeypatch, tmp_path)

    print(f"\n[disabled]  wall_clock_tps={disabled.wall_clock_tps:.2f}  cpu_time_total_delta_s={disabled.cpu_time_total_delta_s:.3f}")
    print(f"[inprocess] wall_clock_tps={inprocess.wall_clock_tps:.2f}  cpu_time_total_delta_s={inprocess.cpu_time_total_delta_s:.3f}")
    if broker is not None:
        print(f"[broker]    wall_clock_tps={broker.wall_clock_tps:.2f}  cpu_time_total_delta_s={broker.cpu_time_total_delta_s:.3f}")
    else:
        print("[broker]    SKIPPED -- REDIS_AVAILABLE probe failed, no Redis reachable at localhost:6379")

    assert disabled.cpu_time_total_delta_s > 0
    assert inprocess.cpu_time_total_delta_s > 0
    if broker is not None:
        assert broker.cpu_time_total_delta_s > 0


# --- Regression guards (Step 6) -------------------------------------------------
#
# Thresholds locked from docs/performance/simq_isolation_overhead.md's committed
# measurement (Step 4/5). Relative, band-tolerance assertions only -- per
# perf_baseline_policy.md Section 3's convention, never an absolute wall-clock or
# CPU-ms literal.

INPROCESS_CPU_OVERHEAD_BAND_PCT = 25.0
BROKER_CPU_OVERHEAD_BAND_PCT = 30.0


@pytest.mark.slow
def test_inprocess_simq_overhead_within_regression_band(monkeypatch):
    """AC (Scope): in-process SimQ engine-CPU overhead vs. the
    QUALITY_SCORING_DISABLED=1 baseline stays under the locked band."""
    disabled = _run_mode_disabled(monkeypatch)
    inprocess = _run_mode_inprocess(monkeypatch)

    assert disabled.cpu_time_total_delta_s > 0, "baseline CPU delta must be positive to compute a ratio"
    overhead_pct = (
        (inprocess.cpu_time_total_delta_s - disabled.cpu_time_total_delta_s)
        / disabled.cpu_time_total_delta_s
        * 100.0
    )
    print(f"\nin-process overhead vs disabled baseline: {overhead_pct:.2f}% (band: {INPROCESS_CPU_OVERHEAD_BAND_PCT}%)")
    assert_perf_threshold(
        overhead_pct, INPROCESS_CPU_OVERHEAD_BAND_PCT,
        "in-process SimQ CPU overhead vs disabled baseline (band locked in "
        "docs/performance/simq_isolation_overhead.md)", op="<",
    )


@pytest.mark.slow
def test_broker_mode_engine_cpu_within_disabled_band(monkeypatch, tmp_path):
    """AC #2: broker mode's engine-process CPU stays within the agreed band of the
    disabled baseline. Skips (does not fail) if Redis is unavailable."""
    if not REDIS_AVAILABLE:
        pytest.skip("REDIS_AVAILABLE probe failed -- no Redis reachable at localhost:6379")

    disabled = _run_mode_disabled(monkeypatch)
    broker = _run_mode_broker(monkeypatch, tmp_path)
    assert broker is not None

    assert disabled.cpu_time_total_delta_s > 0
    overhead_pct = (
        (broker.cpu_time_total_delta_s - disabled.cpu_time_total_delta_s)
        / disabled.cpu_time_total_delta_s
        * 100.0
    )
    print(f"\nbroker overhead vs disabled baseline: {overhead_pct:.2f}% (band: {BROKER_CPU_OVERHEAD_BAND_PCT}%)")
    assert_perf_threshold(
        overhead_pct, BROKER_CPU_OVERHEAD_BAND_PCT,
        "broker-mode engine-process CPU overhead vs disabled baseline (band locked in "
        "docs/performance/simq_isolation_overhead.md)", op="<",
    )


# --- Push-shaper registry cumulative overhead gate (TCK-20260806-PUSH-SHAPER- ------------------
# PERF-REGRESSION-GATE) -------------------------------------------------------------------------
#
# Standing, committed gate for src/observability/event_shapers.py's cumulative CPU cost, so
# overhead accumulation across future migration phases (Phase 2 adds ~4-5x more shapers than
# Phase 1's COMBAT/ECONOMY/FACTION) is caught automatically instead of re-measured by hand once
# per phase. Threshold locked from docs/performance/simq_isolation_overhead.md's "Push-Shaper
# Registry Overhead" section, per perf_baseline_policy.md Section 3's band-tolerance convention.

PUSH_SHAPER_CPU_OVERHEAD_BAND_PCT = 25.0


@pytest.mark.slow
def test_push_shaper_registry_overhead_benchmark(monkeypatch):
    """Produces engine-process CPU time for ENABLE_PUSH_EVENT_SHAPERS=ON vs OFF under the
    `inprocess` SimQ mode. See docs/performance/simq_isolation_overhead.md for the committed
    results table this test's output feeds."""
    shapers_off = _run_mode_inprocess_with_shaper_flag(monkeypatch, shapers_on=False)
    shapers_on = _run_mode_inprocess_with_shaper_flag(monkeypatch, shapers_on=True)

    print(f"\n[shapers_off] wall_clock_tps={shapers_off.wall_clock_tps:.2f}  cpu_time_total_delta_s={shapers_off.cpu_time_total_delta_s:.3f}")
    print(f"[shapers_on]  wall_clock_tps={shapers_on.wall_clock_tps:.2f}  cpu_time_total_delta_s={shapers_on.cpu_time_total_delta_s:.3f}")

    assert shapers_off.cpu_time_total_delta_s > 0
    assert shapers_on.cpu_time_total_delta_s > 0


@pytest.mark.slow
def test_push_shaper_registry_overhead_within_regression_band(monkeypatch):
    """Standing regression gate: apply-layer shaper-registry CPU overhead vs. the
    ENABLE_PUSH_EVENT_SHAPERS=OFF (old diffing-extractor) baseline stays under the locked band,
    under the `inprocess` SimQ mode (the live default)."""
    shapers_off = _run_mode_inprocess_with_shaper_flag(monkeypatch, shapers_on=False)
    shapers_on = _run_mode_inprocess_with_shaper_flag(monkeypatch, shapers_on=True)

    assert shapers_off.cpu_time_total_delta_s > 0, "baseline CPU delta must be positive to compute a ratio"
    overhead_pct = (
        (shapers_on.cpu_time_total_delta_s - shapers_off.cpu_time_total_delta_s)
        / shapers_off.cpu_time_total_delta_s
        * 100.0
    )
    print(f"\npush-shaper-registry overhead vs OFF baseline: {overhead_pct:.2f}% (band: {PUSH_SHAPER_CPU_OVERHEAD_BAND_PCT}%)")
    assert_perf_threshold(
        overhead_pct, PUSH_SHAPER_CPU_OVERHEAD_BAND_PCT,
        "push-shaper-registry CPU overhead vs OFF baseline (band locked in "
        "docs/performance/simq_isolation_overhead.md)", op="<",
    )


# --- Phase 2 push-shaper registry overhead gate (TCK-20260806-PUSH-SHADOW-VALIDATION- -----------
# PERF-PHASE2) -------------------------------------------------------------------------------
#
# Full-registry re-validation: all 5 Phase 2 shapers (StrategyShaper/ProgressionShaper/
# WorldDynamicsShaper/SocialShaper/DeferredInstrumentationShaper) together, on top of Phase 1's
# already-committed cost above. Same band-tolerance convention.

PHASE2_CPU_OVERHEAD_BAND_PCT = 25.0


@pytest.mark.slow
def test_phase2_shaper_registry_overhead_benchmark(monkeypatch):
    """Produces engine-process CPU time for ENABLE_PUSH_EVENT_SHAPERS_PHASE2=ON vs OFF (the
    complete Phase 2 registry) under the `inprocess` SimQ mode."""
    phase2_off = _run_mode_inprocess_with_phase2_flag(monkeypatch, phase2_on=False)
    phase2_on = _run_mode_inprocess_with_phase2_flag(monkeypatch, phase2_on=True)

    print(f"\n[phase2_off] wall_clock_tps={phase2_off.wall_clock_tps:.2f}  cpu_time_total_delta_s={phase2_off.cpu_time_total_delta_s:.3f}")
    print(f"[phase2_on]  wall_clock_tps={phase2_on.wall_clock_tps:.2f}  cpu_time_total_delta_s={phase2_on.cpu_time_total_delta_s:.3f}")

    assert phase2_off.cpu_time_total_delta_s > 0
    assert phase2_on.cpu_time_total_delta_s > 0


@pytest.mark.slow
def test_phase2_shaper_registry_overhead_within_regression_band(monkeypatch):
    """Standing regression gate: the complete Phase 2 shaper registry's CPU overhead vs. the
    ENABLE_PUSH_EVENT_SHAPERS_PHASE2=OFF baseline stays under the locked band, under the
    `inprocess` SimQ mode."""
    phase2_off = _run_mode_inprocess_with_phase2_flag(monkeypatch, phase2_on=False)
    phase2_on = _run_mode_inprocess_with_phase2_flag(monkeypatch, phase2_on=True)

    assert phase2_off.cpu_time_total_delta_s > 0, "baseline CPU delta must be positive to compute a ratio"
    overhead_pct = (
        (phase2_on.cpu_time_total_delta_s - phase2_off.cpu_time_total_delta_s)
        / phase2_off.cpu_time_total_delta_s
        * 100.0
    )
    print(f"\nPhase 2 shaper-registry overhead vs OFF baseline: {overhead_pct:.2f}% (band: {PHASE2_CPU_OVERHEAD_BAND_PCT}%)")
    assert_perf_threshold(
        overhead_pct, PHASE2_CPU_OVERHEAD_BAND_PCT,
        "Phase 2 shaper-registry CPU overhead vs OFF baseline (band locked in "
        "docs/performance/simq_isolation_overhead.md)", op="<",
    )
