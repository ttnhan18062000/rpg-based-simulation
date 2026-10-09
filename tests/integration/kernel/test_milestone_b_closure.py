import pytest
import time
from unittest.mock import MagicMock
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState, EntityState
from src.core.builder import V2EntityBuilder
from src.core.governance import RuntimeMode, PressureSignals
from src.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
from src.engine.worker_logic import default_simulation_worker

@pytest.fixture
def mb_profile():
    return RuntimeProfile(
        name="mb_gate",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1000,
        max_cpu_percent=100.0,
        max_worker_count=4,
        max_queue_depth=10,
        max_replay_buffer_kb=1000,
        max_tick_budget_ms=100.0,
        max_observability_budget_percent=5.0,
        # Milestone B Truth Controls
        sampling_interval_ticks=1,
        dwell_time_ticks=5,
        confidence_window_ticks=3,
        recovery_watermark=0.8
    )

@pytest.fixture
def initial_state():
    return AuthoritativeState(tick=0, seed=1)

class TickKeyedClock:
    """Fake ``time.perf_counter_ns`` whose reading depends on the tick, not on call count.

    Within one tick the first reading is the tick's base time and every later
    reading is ``base + compute_ms``. The kernel measures a tick as a difference
    of two readings: ``_final_compute_ms`` at the end of ``_phase_advancement``
    (the start-to-record span that feeds the governor's ``PressureSignals``) and
    the phase-cost sum behind the budget watchdog. Both therefore come out as
    ``compute_ms`` however many timing calls the kernel makes per tick, so the
    test drives the governor's thresholds and not the kernel's instrumentation
    density. Call ``begin_tick`` before each ``tick_once``.
    """

    def __init__(self, compute_ms: float):
        self._compute_ns = int(compute_ms * 1_000_000)
        self._base_ns = 0
        self._called_this_tick = False

    def begin_tick(self) -> None:
        self._base_ns += 1_000_000_000
        self._called_this_tick = False

    def __call__(self) -> int:
        if not self._called_this_tick:
            self._called_this_tick = True
            return self._base_ns
        return self._base_ns + self._compute_ns


def _tick_with_clock(kernel, clock: TickKeyedClock) -> None:
    clock.begin_tick()
    kernel.tick_once()


@pytest.fixture
def mb_kernel(mb_profile, initial_state):
    from src.platform.rng import DeterministicRNG
    kernel = Kernel(mb_profile, initial_state, DeterministicRNG(1))
    try:
        # Mock RSS to be low (100MB)
        kernel._collector._process.memory_info = MagicMock(return_value=MagicMock(rss=100 * 1024 * 1024))
        yield kernel
    finally:
        kernel.shutdown()


def test_milestone_b_operational_gate(mb_kernel):
    """
    Unified Certification Gate for Milestone B.
    Sequence: NORMAL -> Saturation -> DEGRADED -> NORMAL.
    Verify: Signal Truth, Elasticity, and Hysteresis.

    Pressure is injected through a tick-keyed fake clock (see ``TickKeyedClock``):
    120 ms of compute per tick, between the DEGRADED threshold (100 ms) and the
    SURVIVAL threshold (150 ms), independent of how many timing calls a tick makes.
    """
    from unittest.mock import patch
    kernel = mb_kernel

    # ---------------------------------------------------------
    # Phase 1: Normal Stabilization
    # ---------------------------------------------------------
    for i in range(5):
        kernel.tick_once()
        assert kernel.status.current_mode == RuntimeMode.NORMAL

    # ---------------------------------------------------------
    # Phase 2 & 3: Saturation + Escalation to DEGRADED
    # ---------------------------------------------------------
    clock = TickKeyedClock(compute_ms=120.0)
    modes = []
    with patch('time.perf_counter_ns', side_effect=clock):
        for i in range(10):
            _tick_with_clock(kernel, clock)
            modes.append(kernel.status.current_mode)
            if kernel.status.current_mode == RuntimeMode.DEGRADED:
                break

    assert kernel.status.current_mode == RuntimeMode.DEGRADED
    assert RuntimeMode.SURVIVAL not in modes
    assert kernel.status.signal_history[-1].tick_compute_ms == pytest.approx(120.0)

    # ---------------------------------------------------------
    # Phase 4: Elastic Concurrency (Policy Verification)
    # ---------------------------------------------------------
    # In DEGRADED mode, verify worker pool uses only 50% capacity (2 workers)

    from src.core.work import WorkClass
    packets = [
        WorkerPacket(packet_id=f"p{i}", work_id=f"w:{i}", tick=0, world_time=0, seed=i,
                     work_class=WorkClass.CRITICAL,
                     subject=(V2EntityBuilder(i+1)
                              .kind("TEST")
                              .location(0.0, 0.0)
                              .build()),
                     neighbor_view=[], work_kind="TEST", payload={})
        for i in range(10)
    ]

    kernel._worker_manager.reset_tick_stats()
    kernel._worker_manager.execute_batch(packets, default_simulation_worker, concurrency_limit=kernel._current_policy.concurrency_limit)

    # Peak workers in DEGRADED should be capped at 2 (50% of 4)
    assert kernel._worker_manager.get_stats()["peak_workers"] <= 2

    # ---------------------------------------------------------
    # Phase 5: Hysteresis-Gated Recovery
    # ---------------------------------------------------------
    # The patch has ended (pressure gone). Recovery needs dwell + confidence ticks.
    for i in range(25):
        kernel.tick_once()
        if kernel.status.current_mode == RuntimeMode.NORMAL:
            break

    assert kernel.status.current_mode == RuntimeMode.NORMAL


def test_milestone_b_gate_reaches_survival_at_injected_150ms_plus(mb_kernel):
    """Negative control: the fake clock still drives the governor.

    The same clock at 160 ms (above the 1.5x SURVIVAL threshold of 150 ms) must
    escalate to SURVIVAL, so the DEGRADED verdict above is not an artefact of the
    fake ignoring its input.
    """
    from unittest.mock import patch
    kernel = mb_kernel
    for i in range(5):
        kernel.tick_once()
    clock = TickKeyedClock(compute_ms=160.0)
    with patch('time.perf_counter_ns', side_effect=clock):
        for i in range(10):
            _tick_with_clock(kernel, clock)
            if kernel.status.current_mode == RuntimeMode.SURVIVAL:
                break
    assert kernel.status.current_mode == RuntimeMode.SURVIVAL
    assert kernel.status.signal_history[-1].tick_compute_ms == pytest.approx(160.0)


@pytest.mark.slow
def test_milestone_b_memory_survival_gate(mb_profile, initial_state):
    """Verify SURVIVAL mode escalation via Memory pressure."""
    from src.platform.rng import DeterministicRNG
    rng = DeterministicRNG(1)
    kernel = Kernel(mb_profile, initial_state, rng)
    try:
        # Mock memory collector to report critical overload (> 1000MB)
        kernel._collector._process.memory_info = MagicMock(return_value=MagicMock(rss=1100 * 1024 * 1024))

        kernel.tick_once()
        assert kernel.status.current_mode == RuntimeMode.SURVIVAL

        # Verify Policy in SURVIVAL: Concurrency Limit = 0.25 (1 worker)
        # Even if we have 100 entities, strictly 1 at a time.
        # Note: Kernel advancement records the signal.
        assert kernel.status.signal_history[-1].active_workers <= 1
    finally:
        kernel.shutdown()
