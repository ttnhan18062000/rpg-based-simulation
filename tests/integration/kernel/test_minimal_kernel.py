from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG


def test_tick_advancement():
    """Verify that tick_once increases tick and world_time exactly once."""
    profile = RuntimeProfile(
        name="test-m2",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=16.6
    )
    state = AuthoritativeState(tick=0, seed=42, world_time=100)
    rng = DeterministicRNG(42)
    kernel = Kernel(profile, state, rng)
    try:
        kernel.tick_once()
        assert kernel.state.tick == 1
        assert kernel.state.world_time == 101

        kernel.tick_once()
        assert kernel.state.tick == 2
        assert kernel.state.world_time == 102
    finally:
        kernel.shutdown()


def test_quiet_tick_validity():
    """Verify that a tick with no entities still progresses world time."""
    from src.config.profiles import HardwareClass
    # State with no entities
    profile = RuntimeProfile(
        name="test-quiet",
        hardware_class=HardwareClass.CLASS_C,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=1,
        max_queue_depth=10,
        max_work_debt=10,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=100.0
    )
    state = AuthoritativeState(tick=10, seed=1, world_time=500, entities={})
    rng = DeterministicRNG(1)
    kernel = Kernel(profile, state, rng)
    try:
        kernel.tick_once()
        assert kernel.state.tick == 11
        assert kernel.state.world_time == 501
    finally:
        kernel.shutdown()
