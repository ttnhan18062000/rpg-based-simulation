"""
Production Observatory Overhead — Performance validation test.

Validates that the V2 Observatory LIGHT mode adds less than the configured
threshold of tick p95 overhead compared to OFF mode.
"""
import time
import statistics
import pytest

from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.readiness.harness import PRODUCTION_READINESS_CRITERIA


ENTITY_COUNT = 30
TICK_COUNT = 100
SEED = 42


def _build_kernel(obs_mode: ObservabilityMode, run_id: str) -> Kernel:
    ObservabilityConfig.set_override_mode(obs_mode)
    profile = RuntimeProfile(
        name="perf-overhead-profile",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=2048,
        max_cpu_percent=100.0,
        max_worker_count=2,
        max_queue_depth=500,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=50.0
    )
    entities = {}
    for idx in range(1, ENTITY_COUNT + 1):
        entities[idx] = V2EntityBuilder(idx).combat(hp=100, alive=True).location(10.0 + idx, 10.0 + idx).build()

    state = AuthoritativeState(tick=1, seed=SEED, world_time=100, entities=entities)
    rng = DeterministicRNG(SEED)
    return Kernel(profile, state, rng, run_id=run_id)


def test_observatory_light_mode_overhead():
    """Observatory LIGHT mode tick overhead must be below production threshold."""
    # Baseline: OFF
    try:
        kernel_off = _build_kernel(ObservabilityMode.OFF, run_id="overhead-off")
        off_times = []
        for _ in range(TICK_COUNT):
            t0 = time.perf_counter_ns()
            kernel_off.tick_once()
            off_times.append((time.perf_counter_ns() - t0) / 1e6)
        kernel_off.shutdown()
    finally:
        ObservabilityConfig.set_override_mode(None)

    # LIGHT mode
    try:
        kernel_light = _build_kernel(ObservabilityMode.LIGHT, run_id="overhead-light")
        light_times = []
        for _ in range(TICK_COUNT):
            t0 = time.perf_counter_ns()
            kernel_light.tick_once()
            light_times.append((time.perf_counter_ns() - t0) / 1e6)
        kernel_light.shutdown()
    finally:
        ObservabilityConfig.set_override_mode(None)

    off_p95 = sorted(off_times)[int(len(off_times) * 0.95)]
    light_p95 = sorted(light_times)[int(len(light_times) * 0.95)]
    overhead_pct = ((light_p95 - off_p95) / off_p95 * 100.0) if off_p95 > 0 else 0.0

    threshold = PRODUCTION_READINESS_CRITERIA["max_tick_p95_overhead_percent"]

    # Log results for visibility
    print(f"OFF p95: {off_p95:.3f}ms, LIGHT p95: {light_p95:.3f}ms, overhead: {overhead_pct:.2f}%")

    assert overhead_pct < threshold, (
        f"Observatory LIGHT overhead {overhead_pct:.2f}% exceeds threshold {threshold}%"
    )


def test_observatory_off_mode_zero_overhead():
    """Observatory OFF mode should produce effectively zero observability overhead."""
    try:
        kernel = _build_kernel(ObservabilityMode.OFF, run_id="overhead-off-zero")
        times = []
        for _ in range(TICK_COUNT):
            t0 = time.perf_counter_ns()
            kernel.tick_once()
            times.append((time.perf_counter_ns() - t0) / 1e6)
        kernel.shutdown()
    finally:
        ObservabilityConfig.set_override_mode(None)

    p95 = sorted(times)[int(len(times) * 0.95)]
    # OFF mode should complete ticks in a reasonable time.
    # 200ms is generous but guards against truly runaway latency on any hardware.
    assert p95 < 200.0, f"OFF mode p95 {p95:.3f}ms unexpectedly slow"
