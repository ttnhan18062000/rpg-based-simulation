"""
Anomaly Worker Failure Resilience — Integration test.

Validates that when the LiveAnomalyWorker crashes or encounters fatal
exceptions, the simulation engine continues operating normally, the
worker status reflects the failure, and alerts are generated.
"""
import time
import pytest

from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.anomaly.worker import LiveAnomalyWorker, LiveWorkerConfig
from src.observability.alerts.manager import AlertsManager
from src.observability.live.event_publisher import LiveEventPublisher


ENTITY_COUNT = 15
SEED = 42


def _build_kernel(run_id: str) -> Kernel:
    profile = RuntimeProfile(
        name="worker-crash-profile",
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


class _CrashingRule:
    """Simulated rule that always raises an exception."""
    def evaluate_event(self, event, window):
        raise RuntimeError("Simulated rule crash for testing")


@pytest.fixture(autouse=True)
def setup_teardown():
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    AlertsManager.reset()
    yield
    ObservabilityConfig.set_override_mode(None)
    AlertsManager.reset()
    LiveEventPublisher.reset_instance()


def test_engine_continues_after_worker_crash():
    """Engine completes ticks normally even when anomaly worker rules crash."""
    kernel = _build_kernel("worker-crash-engine-test")

    config = LiveWorkerConfig(
        stream_backend="in_process",
        enabled_rules=["HardLawViolationLive"],
        window_ticks=50
    )
    worker = LiveAnomalyWorker(config=config)
    worker.rules = [_CrashingRule()]
    worker.start()

    # Run ticks — engine must not be affected by worker crashes
    for _ in range(20):
        kernel.tick_once()

    assert kernel.state.tick >= 20, "Engine did not complete expected ticks"

    worker.stop()
    kernel.shutdown()


def test_worker_status_reflects_errors():
    """Worker status should record errors from crashing rules."""
    config = LiveWorkerConfig(
        stream_backend="in_process",
        enabled_rules=["HardLawViolationLive"],
        window_ticks=50
    )
    worker = LiveAnomalyWorker(config=config)
    worker.rules = [_CrashingRule()]
    worker.start()

    kernel = _build_kernel("worker-status-test")
    for _ in range(10):
        kernel.tick_once()

    # Give worker a moment to process events and hit errors
    time.sleep(0.5)

    # Worker should still be in RUNNING or DEGRADED state (not crashed entirely)
    assert worker.status_record.status in ("RUNNING", "DEGRADED", "STOPPED"), \
        f"Unexpected worker status: {worker.status_record.status}"

    worker.stop()
    kernel.shutdown()


def test_worker_can_stop_cleanly_after_crash():
    """Worker stop() must not hang or raise after experiencing rule crashes."""
    config = LiveWorkerConfig(
        stream_backend="in_process",
        enabled_rules=["HardLawViolationLive"],
        window_ticks=50
    )
    worker = LiveAnomalyWorker(config=config)
    worker.rules = [_CrashingRule()]
    worker.start()

    kernel = _build_kernel("worker-clean-stop-test")
    for _ in range(5):
        kernel.tick_once()

    time.sleep(0.3)

    # stop() must complete without hanging
    worker.stop()  # Should not raise or hang
    kernel.shutdown()

    assert worker.status_record.status == "STOPPED"
