"""Replay-diff helper: one in-envelope case, plus one violation per envelope dimension."""

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.core.state import AuthoritativeState
from tests.helpers import replay_diff as rd
from tests.integration.kernel import test_determinism_suite as suite


def _state():
    e1 = V2EntityBuilder(1).location(0.0, 0.0).identity(role=EntityRole.HERO).build()
    e2 = V2EntityBuilder(2).location(5.0, 5.0).identity(role=EntityRole.MONSTER).build()
    return AuthoritativeState(tick=0, seed=suite.REPRODUCIBILITY_SEED, world_time=0, entities={1: e1, 2: e2})


def test_envelope_bounds_come_from_the_determinism_suite():
    assert rd.REPRODUCIBILITY_SEED is suite.REPRODUCIBILITY_SEED
    assert rd.REPRODUCIBILITY_TICKS is suite.REPRODUCIBILITY_TICKS
    assert rd.REPRODUCIBILITY_PROFILE is suite.REPRODUCIBILITY_PROFILE


def test_inside_envelope_is_replayed_and_identical():
    result = rd.replay_diff(_state, seed=suite.REPRODUCIBILITY_SEED, ticks=suite.REPRODUCIBILITY_TICKS)
    assert result.verdict == rd.IDENTICAL
    assert len(result.hashes) == 2 and result.hashes[0] == result.hashes[1]
    assert (result.seed, result.ticks, result.executor, result.world_source) == (
        suite.REPRODUCIBILITY_SEED, suite.REPRODUCIBILITY_TICKS, "default", "hand-built")
    assert result.profile == suite.REPRODUCIBILITY_PROFILE.name


def _never_built():
    raise AssertionError("outside the envelope the helper must not run anything")


def test_not_hand_built_is_outside_verified_scope():
    result = rd.replay_diff(_never_built, seed=suite.REPRODUCIBILITY_SEED, ticks=1, world_source="compiled")
    assert result.verdict == rd.OUTSIDE_VERIFIED_SCOPE
    assert "world_source" in result.reasons[0]


def test_unseeded_is_outside_verified_scope():
    result = rd.replay_diff(_never_built, seed=None, ticks=1)
    assert result.verdict == rd.OUTSIDE_VERIFIED_SCOPE and "unseeded" in result.reasons[0]


def test_different_seed_is_outside_verified_scope():
    result = rd.replay_diff(_never_built, seed=suite.REPRODUCIBILITY_SEED + 1, ticks=1)
    assert result.verdict == rd.OUTSIDE_VERIFIED_SCOPE and "seed" in result.reasons[0]


def test_one_tick_past_the_bound_is_outside_verified_scope():
    result = rd.replay_diff(_never_built, seed=suite.REPRODUCIBILITY_SEED, ticks=suite.REPRODUCIBILITY_TICKS + 1)
    assert result.verdict == rd.OUTSIDE_VERIFIED_SCOPE and "ticks" in result.reasons[0]


def test_different_profile_is_outside_verified_scope():
    other = RuntimeProfile(name="other", hardware_class=HardwareClass.CLASS_B, max_ram_mb=1024, max_cpu_percent=100.0,
                           max_worker_count=1, max_queue_depth=100, max_replay_buffer_kb=0,
                           max_observability_budget_percent=0.0, max_tick_budget_ms=16.6)
    result = rd.replay_diff(_never_built, seed=suite.REPRODUCIBILITY_SEED, ticks=1, profile=other)
    assert result.verdict == rd.OUTSIDE_VERIFIED_SCOPE and "profile" in result.reasons[0]


def test_multiple_violations_are_all_listed():
    result = rd.replay_diff(_never_built, seed=None, ticks=suite.REPRODUCIBILITY_TICKS + 1, world_source="compiled")
    assert len(result.reasons) == 3
