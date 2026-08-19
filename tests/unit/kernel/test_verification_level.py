import pytest
from src.core.state import AuthoritativeState, RegionState
from src.core.governance import RuntimeMode
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG


def get_test_profile():
    return RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_C,
        max_ram_mb=512,
        max_cpu_percent=50,
        max_worker_count=0,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5,
        max_tick_budget_ms=100.0,
        sampling_interval_ticks=1
    )


@pytest.fixture
def base_state():
    region = RegionState(
        id="r1",
        name="Region 1",
        kind="FOREST",
        bounds=(0, 0, 100, 100),
        hazard_level=0.1
    )
    return AuthoritativeState(
        tick=1,
        seed=12345,
        world_time=0,
        regions={"r1": region},
        next_entity_id=1,
        next_node_id=1000,
        terrain={(x, y): "FLOOR" for x in range(0, 10) for y in range(0, 10)}
    )


def test_shutdown_result_flags_reduced_verification_after_degraded_run(base_state):
    """
    Cumulative-tracking case: a run that dipped into DEGRADED and recovered to NORMAL
    before shutdown() must still report REDUCED verification (investigation.md §5).
    """
    profile = get_test_profile()
    rng = DeterministicRNG(base_state.seed)
    kernel = Kernel(profile, base_state, rng)
    kernel._status.reset_dwell(RuntimeMode.DEGRADED, kernel._state.tick)
    kernel._status.reset_dwell(RuntimeMode.NORMAL, kernel._state.tick + 1)

    assert kernel._status.current_mode == RuntimeMode.NORMAL
    assert kernel._status.max_mode_reached == RuntimeMode.DEGRADED

    result = kernel.shutdown()
    assert result.verification_level == "REDUCED"


def test_shutdown_result_full_verification_on_normal_run(base_state):
    """
    Regression guard: a run that never leaves NORMAL/CONSTRAINED reports FULL
    verification — the new field must not default to REDUCED incorrectly.
    """
    profile = get_test_profile()
    rng = DeterministicRNG(base_state.seed)
    kernel = Kernel(profile, base_state, rng)
    kernel._status.reset_dwell(RuntimeMode.CONSTRAINED, kernel._state.tick)
    kernel._status.reset_dwell(RuntimeMode.NORMAL, kernel._state.tick + 1)

    assert kernel._status.max_mode_reached == RuntimeMode.CONSTRAINED

    result = kernel.shutdown()
    assert result.verification_level == "FULL"


def test_shutdown_result_flags_reduced_verification_after_survival_run(base_state):
    """
    SURVIVAL mode has replay_allowed=False (no TICK_END trail to scan) — the
    verification_level derivation must read max_mode_reached directly, not scan
    the replay stream, so it still works with no TICK_END events at all.
    """
    profile = get_test_profile()
    rng = DeterministicRNG(base_state.seed)
    kernel = Kernel(profile, base_state, rng)
    kernel._status.reset_dwell(RuntimeMode.SURVIVAL, kernel._state.tick)

    assert kernel._status.max_mode_reached == RuntimeMode.SURVIVAL

    result = kernel.shutdown()
    assert result.verification_level == "REDUCED"
