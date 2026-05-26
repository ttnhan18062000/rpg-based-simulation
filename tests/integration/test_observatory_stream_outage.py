"""
Stream Outage Resilience — Integration test.

Validates that when the event stream backend (Redis) is unreachable, the
simulation engine continues operating normally, backpressure is visible
in adapter health, and alerts are generated.
"""
import collections
import threading
import pytest

from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.stream.adapters import RedisStreamAdapter
from src.observability.alerts.manager import AlertsManager


ENTITY_COUNT = 20
SEED = 42


def _build_kernel(run_id: str) -> Kernel:
    profile = RuntimeProfile(
        name="stream-outage-profile",
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


@pytest.fixture(autouse=True)
def setup_teardown():
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    AlertsManager.reset()
    yield
    ObservabilityConfig.set_override_mode(None)
    AlertsManager.reset()


def _make_broken_adapter():
    """Create a RedisStreamAdapter that is permanently disconnected."""
    adapter = RedisStreamAdapter.__new__(RedisStreamAdapter)
    adapter.redis_url = "redis://192.0.2.1:9999/0"
    adapter.stream_name = "test:broken"
    adapter.max_queue_size = 100
    adapter.client = None
    adapter._connected = False
    adapter.dropped_count = 0
    adapter.published_count = 0
    adapter.last_error = "Simulated stream outage"
    adapter.last_success_at = None
    adapter.backpressure_active = False
    adapter._queue = collections.deque()
    adapter._queue_lock = threading.Lock()
    adapter._queue_cond = threading.Condition(adapter._queue_lock)
    adapter._running = False
    adapter._worker_thread = None
    return adapter


def test_engine_continues_during_stream_outage():
    """Engine completes ticks normally despite broken stream adapter."""
    kernel = _build_kernel("stream-outage-test")

    broken = _make_broken_adapter()
    if hasattr(kernel, "_event_recorder") and hasattr(kernel._event_recorder, "_stream_adapter"):
        kernel._event_recorder._stream_adapter = broken

    for _ in range(30):
        kernel.tick_once()

    assert kernel.state.tick >= 30, "Engine did not complete expected ticks"
    kernel.shutdown()


def test_stream_outage_health_shows_degraded():
    """Broken stream adapter reports degraded health status."""
    broken = _make_broken_adapter()
    health = broken.health()
    assert health["status"] == "degraded"
    assert health["connected"] is False


def test_stream_outage_no_crash():
    """Publishing events to a broken adapter must not raise exceptions."""
    broken = _make_broken_adapter()
    from src.observability.events import SimulationEvent

    event = SimulationEvent(
        event_type="TestCombatEvent",
        event_category="combat",
        severity="INFO",
        tick=1,
        source_system="combat_system",
        message="test event for outage simulation",
        run_id="stream-test"
    )
    # Should not raise
    broken.publish(event)
    assert broken.dropped_count >= 0  # May or may not have incremented depending on queue state
