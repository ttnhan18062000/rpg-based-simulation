"""Health never exceeds max_hp: the combat patch writer clamps, so every CombatUpdate obeys the bound (inn REST at full health used to leave
a body at 105/100). The invariant is also checked over a short real kernel run."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.updates import CombatUpdate
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.patches import CombatPatch
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world


def _apply(hp, max_hp, **update):
    ent = V2EntityBuilder(1).kind("human").combat(hp=hp, max_hp=max_hp, alive=True).build()
    changes: dict = {}
    CombatPatch(entity_id=1, combat=CombatUpdate(**update)).apply(ent, changes)
    return changes["combat"]


def test_a_rest_at_full_health_stays_at_max_hp():
    assert _apply(100, 100, hp_delta=5).hp == 100


def test_a_rest_a_few_points_short_rises_to_max_hp_and_no_further():
    assert _apply(97, 100, hp_delta=5).hp == 100


def test_a_heal_below_max_is_untouched_and_damage_still_lands():
    assert _apply(50, 100, hp_delta=5).hp == 55
    assert _apply(50, 100, hp_delta=-20).hp == 30
    assert _apply(5, 100, hp_delta=-20).hp == 0


def test_a_raise_of_max_hp_and_hp_in_one_update_stays_consistent():
    after = _apply(100, 100, hp_delta=10, max_hp_delta=10)
    assert (after.hp, after.max_hp) == (110, 110)


def test_a_lowered_max_hp_pulls_hp_down_with_it():
    after = _apply(100, 100, hp_delta=0, max_hp_delta=-20)
    assert (after.hp, after.max_hp) == (80, 80)


@pytest.mark.extra_slow
def test_no_living_body_ends_a_kernel_run_above_max_hp():
    state = compile_world("frontier_living_world", 42)
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
                    flags={"no_frame_pacing": True}, executor=LocalSequentialExecutor(), governor=PinnedNormalGovernor())
    try:
        for _ in range(700):  # the plant-eater herd first rested at an inn above max around tick 516
            kernel.tick_once()
            over = [e.id for e in kernel._state.entities.values() if e.combat.alive and e.combat.hp > e.combat.max_hp]
            assert not over, f"tick {kernel._state.tick}: bodies above max_hp: {over}"
    finally:
        kernel.shutdown()
