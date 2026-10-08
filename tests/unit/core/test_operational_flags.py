import pytest
from src.config.profiles import RuntimeProfile, HardwareClass
from src.config.validator import ProfileValidator, ConfigValidationError
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from unittest.mock import MagicMock


def test_safe_operational_flags_accepted(tmp_path):
    """
    M7 Law: Support narrow, safe operational flags.

    This only proves a kernel built with these flags does not raise. It is NOT proof that a flag is obeyed: `FORCE_REPLAY_OFF` and
    `MINIMAL_DIAGNOSTICS` are read nowhere in `src/` (see `test_unimplemented_operational_flags_change_nothing`); the kernel's own switch
    is `no_replay` (`test_no_replay_stops_the_replay_sink`).
    """
    profile = RuntimeProfile(
        name="SAFE_FLAGS",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=4,
        max_queue_depth=1000,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=10.0
    )
    state = AuthoritativeState(tick=0, seed=42)

    # Flags that are explicitly allowed/safe
    safe_flags = {
        "FORCE_REPLAY_OFF": True,
        "MINIMAL_DIAGNOSTICS": True
    }

    # Should not raise
    kernel = Kernel(profile=profile, state=state, rng=MagicMock(), flags=safe_flags)
    try:
        assert kernel._profile.name == "SAFE_FLAGS"
    finally:
        kernel.shutdown()


def test_unsafe_flags_rejected():
    """
    M7 Law: Reject flags that bypass authoritative resource logic.
    """
    unsafe_flags = {"BYPASS_GOVERNOR": True}
    
    with pytest.raises(ConfigValidationError) as exc:
        ProfileValidator.validate_flags(unsafe_flags)
    assert "is FORBIDDEN" in str(exc.value)


def test_flags_cannot_alter_authoritative_semantics():
    """
    M7 Law: Flags must remain subordinate to profile and governor rules.
    Verify that a flag doesn't accidentally change the authoritative outcome.
    """
    from src.engine.checkpoint import CanonicalStateHasher
    from src.platform.rng import DeterministicRNG

    profile = RuntimeProfile(
        name="TEST",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=10,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=16.6
    )
    state = AuthoritativeState(tick=0, seed=42)
    rng = MagicMock(spec=DeterministicRNG)
    rng.get_state.return_value = None

    k1 = Kernel(profile=profile, state=state, rng=rng, flags={"FLAG_A": True})
    k2 = Kernel(profile=profile, state=state, rng=rng, flags={"FLAG_B": True})
    try:
        k1.tick_once()
        hash_a = CanonicalStateHasher.get_hash(k1.state)

        k2.tick_once()
        hash_b = CanonicalStateHasher.get_hash(k2.state)

        # Authoritative outcome must be identical
        assert hash_a == hash_b
        assert k1.state.tick == k2.state.tick
    finally:
        k1.shutdown()
        k2.shutdown()


# --- What the kernel really does with operational flags (TCK-20261006-PERF-OPERATIONAL-FLAGS-MATRIX-DRIFT) -----------------------------

def _flag_profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="FLAG_OBEDIENCE", hardware_class=HardwareClass.CLASS_B, max_ram_mb=1024, max_cpu_percent=100.0, max_worker_count=0,
        max_queue_depth=10, max_replay_buffer_kb=64, max_observability_budget_percent=5.0, max_tick_budget_ms=100000.0,
    )


def _run_with_flags(flags, ticks=3):
    """Run a small kernel with a recording replay manager; return (replay emit count, policy.replay_allowed per tick, final state hash)."""
    from src.engine.checkpoint import CanonicalStateHasher
    from src.perf.scenarios import build_idle_state
    from src.platform.rng import DeterministicRNG

    replay = MagicMock()
    replay.get_stats.return_value = {"backlog_kb": 0}
    replay.replay_metrics.return_value = {"pending_replay_flushes": 0}
    kernel = Kernel(profile=_flag_profile(), state=build_idle_state(entity_count=10), rng=DeterministicRNG(7), replay=replay,
                    flags={"no_frame_pacing": True, **flags})
    allowed_per_tick = [kernel._current_policy.replay_allowed]
    try:
        for _ in range(ticks):
            kernel.tick_once()
            allowed_per_tick.append(kernel._current_policy.replay_allowed)
        return replay.emit.call_count, allowed_per_tick, CanonicalStateHasher.get_hash(kernel.state), kernel._status.current_mode.name
    finally:
        kernel.shutdown()


def test_no_replay_stops_the_replay_sink():
    """`no_replay` is the kernel's real replay switch: replay_allowed is False from construction and after every governor evaluation, and nothing is emitted."""
    emitted_without, allowed_without, hash_without, _ = _run_with_flags({})
    emitted_with, allowed_with, hash_with, _ = _run_with_flags({"no_replay": True})
    assert emitted_without > 0, "the control run never emitted, so a silent sink would prove nothing"
    assert emitted_with == 0
    assert allowed_with == [False] * len(allowed_with)
    assert allowed_without[-1] is True
    assert hash_with == hash_without, "the replay switch must not change the authoritative outcome"


def test_unimplemented_operational_flags_change_nothing():
    """`FORCE_REPLAY_OFF`, `SELECT_PROFILE` and `FORCE_DEGRADED` are documented as not implemented: no code in src/ reads them. If one
    is implemented, this fails and the operational-controls matrix must change with it."""
    baseline = _run_with_flags({})
    for flag in ("FORCE_REPLAY_OFF", "SELECT_PROFILE", "FORCE_DEGRADED", "MINIMAL_DIAGNOSTICS"):
        assert _run_with_flags({flag: True}) == baseline, flag


def test_validated_but_unread_flags_change_nothing():
    """`SURVIVAL_ONLY` and `REPLAY_ENABLED` are checked by `validate_flags` and read by nothing else."""
    baseline = _run_with_flags({})
    assert _run_with_flags({"SURVIVAL_ONLY": True}) == baseline
    assert _run_with_flags({"REPLAY_ENABLED": True}) == baseline


@pytest.mark.parametrize("flag", ["FORCE_NORMAL", "BYPASS_GOVERNOR", "DISABLE_RESOURCE_CEILINGS"])
def test_each_forbidden_flag_is_rejected(flag):
    """The enforced forbidden list (src/config/validator.py), not just the one flag the matrix used to name. Tested on the validator, not by
    constructing a Kernel: a Kernel that rejects a flag in `__init__` has already started its background workers and leaks them."""
    with pytest.raises(ConfigValidationError, match="is FORBIDDEN"):
        ProfileValidator.validate_flags({flag: True})


def test_contradictory_flags_are_rejected():
    with pytest.raises(ConfigValidationError, match="Contradictory Flags"):
        ProfileValidator.validate_flags({"SURVIVAL_ONLY": True, "REPLAY_ENABLED": True})
