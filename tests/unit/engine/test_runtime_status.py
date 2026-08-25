"""
Regression coverage for TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE (AC3): before this ticket's fix,
RuntimeStatus had no declared force_full_scan field, so V2EngineManager._update_latest_state's
getattr(self._kernel.status, "force_full_scan", False) always returned the False default
regardless of how the Kernel was booted.
"""
from src.engine.runtime_status import RuntimeStatus
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG


def _profile(name: str) -> RuntimeProfile:
    return RuntimeProfile(
        name=name,
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=16.6,
    )


def test_runtime_status_default_construction_has_force_full_scan_false():
    assert RuntimeStatus().force_full_scan is False


def test_kernel_status_exposes_force_full_scan_from_boot_flag():
    state = AuthoritativeState(tick=0, seed=42, entities={})
    rng = DeterministicRNG(42)
    kernel = Kernel(_profile("test-force-full-scan-boot-true"), state, rng, flags={"force_full_scan": True})
    try:
        # Boot-time, not tick-derived: true immediately after construction, before tick_once().
        assert kernel.status.force_full_scan is True
    finally:
        kernel.shutdown()


def test_kernel_status_force_full_scan_defaults_false_without_flag():
    state = AuthoritativeState(tick=0, seed=1, entities={})
    rng = DeterministicRNG(1)
    kernel = Kernel(_profile("test-force-full-scan-boot-false"), state, rng)
    try:
        assert kernel.status.force_full_scan is False
    finally:
        kernel.shutdown()

    state2 = AuthoritativeState(tick=0, seed=2, entities={})
    rng2 = DeterministicRNG(2)
    kernel2 = Kernel(_profile("test-force-full-scan-boot-flags-none"), state2, rng2, flags=None)
    try:
        assert kernel2.status.force_full_scan is False
    finally:
        kernel2.shutdown()
