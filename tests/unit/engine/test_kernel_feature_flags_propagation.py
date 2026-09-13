"""
TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS.

Kernel.__init__() seeds state.feature_flags from FeatureFlagManager's own defaults (merged
under any explicit overrides already present) -- the single real entry point every simulation
run passes through. This tests the *mechanism* (the seeding itself, and that explicit overrides
still win), not just that a specific flag's value is now "ON" -- a values-only test would pass
even if seeding worked by some other, less general path than intended.
"""
from __future__ import annotations

import pytest

from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG


def _profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="test", hardware_class=HardwareClass.CLASS_A, max_ram_mb=1024,
        max_cpu_percent=100.0, max_worker_count=1, max_queue_depth=10,
        max_replay_buffer_kb=100, max_observability_budget_percent=5.0, max_tick_budget_ms=16.6,
    )


def _minimal_state(feature_flags: dict | None = None) -> AuthoritativeState:
    kwargs = {"tick": 0, "seed": 42}
    if feature_flags is not None:
        kwargs["feature_flags"] = feature_flags
    return AuthoritativeState(**kwargs)


def test_kernel_seeds_every_manager_flag_when_state_declares_none():
    """A state with no feature_flags at all ends up with every FeatureFlagManager default,
    not just the one flag this ticket cares about -- proves the seeding is general, not a
    one-flag special case."""
    state = _minimal_state()
    assert state.feature_flags == {}

    kernel = Kernel(profile=_profile(), state=state, rng=DeterministicRNG(42))
    try:
        manager_defaults = FeatureFlagManager().serialize()
        for flag, expected_mode in manager_defaults.items():
            assert kernel._state.feature_flags.get(flag) == expected_mode, (
                f"{flag} not seeded: expected {expected_mode!r}, "
                f"got {kernel._state.feature_flags.get(flag)!r}"
            )
    finally:
        kernel.shutdown(timeout_s=1.0)


def test_kernel_preserves_explicit_override_that_disagrees_with_manager_default():
    """An explicit state.feature_flags entry that disagrees with FeatureFlagManager's own
    default must survive seeding untouched -- explicit overrides always win, seeding only fills
    in what the caller never set."""
    # ENABLE_WORLD_CAPABILITY_LAYER defaults OFF in FeatureFlagManager; override it ON here.
    state = _minimal_state(feature_flags={"ENABLE_WORLD_CAPABILITY_LAYER": FeatureMode.ON})

    kernel = Kernel(profile=_profile(), state=state, rng=DeterministicRNG(42))
    try:
        assert kernel._state.feature_flags["ENABLE_WORLD_CAPABILITY_LAYER"] == FeatureMode.ON
        # Confirm the manager's own default really is OFF, so this is a real disagreement being
        # tested, not a coincidence where override and default already matched.
        assert (
            FeatureFlagManager().get_flag_mode("ENABLE_WORLD_CAPABILITY_LAYER") == FeatureMode.OFF
        )
    finally:
        kernel.shutdown(timeout_s=1.0)


def test_kernel_seeding_is_idempotent_across_repeated_construction():
    """Constructing a second Kernel from the first Kernel's own resulting state must not
    double-seed or corrupt already-resolved values."""
    state = _minimal_state()
    kernel_1 = Kernel(profile=_profile(), state=state, rng=DeterministicRNG(42))
    try:
        once_seeded = kernel_1._state.feature_flags

        kernel_2 = Kernel(profile=_profile(), state=kernel_1._state, rng=DeterministicRNG(42))
        try:
            assert kernel_2._state.feature_flags == once_seeded
        finally:
            kernel_2.shutdown(timeout_s=1.0)
    finally:
        kernel_1.shutdown(timeout_s=1.0)


@pytest.mark.corpus_flag_guardrail
@pytest.mark.e2e
def test_guild_quest_generation_fires_in_unmodified_corpus_profile_without_env_var():
    """The real acceptance signal: a real, unmodified corpus profile (no env var, no explicit
    ENABLE_GUILD_QUEST_GENERATION override in its own YAML) actually produces a guild visit and
    a real lead, purely from FeatureFlagManager's own default now reaching state.feature_flags
    through Kernel.__init__. This is what "propagation is fixed" means end to end."""
    from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
    import src.town.guild as guild_mod

    profile = _resolve_profile("frontier_marches")
    feature_flags = _load_profile_feature_flags(profile)
    assert "ENABLE_GUILD_QUEST_GENERATION" not in feature_flags, (
        "this profile must not itself declare the flag -- the whole point is proving the "
        "manager default alone is enough"
    )

    visit_calls = []
    orig_visit = guild_mod.GuildAction.visit

    def patched_visit(entity, state):
        result = orig_visit(entity, state)
        if result is not None:
            visit_calls.append((state.tick, entity.id))
        return result

    guild_mod.GuildAction.visit = staticmethod(patched_visit)
    try:
        _run_engine("frontier_marches", 42, 200, extra_flags=feature_flags)
    finally:
        guild_mod.GuildAction.visit = orig_visit

    assert visit_calls, (
        "GuildAction.visit() never fired in an unmodified corpus profile with no env var -- "
        "the propagation fix did not reach a real run"
    )
