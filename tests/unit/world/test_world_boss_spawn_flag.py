"""Owner decision 14: all three world-boss spawn branches are inert unless ENABLE_WORLD_BOSS_SPAWN is "ON".

The code is kept (flag ON still spawns exactly as before) and no gate or threshold changed. The
three branches: BossService.check_for_boss_spawn (region boss), BossService.check_for_lair_spawn
(Lair occupant), and the calamity boss in CalamityService.process_world_dynamics.
"""
from __future__ import annotations

import pytest

from src.core.state import AuthoritativeState, PlaceKind, PlaceState, RegionState
from src.core.updates import StateUpdate
from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode
from src.engine.world_dynamics import WorldDynamicsSystem
from src.systems.world_systems.generator import EntityGenerator
from src.world.boss import WORLD_BOSS_SPAWN_FLAG, BossService, world_boss_spawn_enabled
from src.world.calamity import CalamityService

ON = {WORLD_BOSS_SPAWN_FLAG: "ON"}


def _gate_open_state(feature_flags=None, with_lair=False):
    region = RegionState(
        id="region_1", name="Dark Forest", bounds=(0, 0, 100, 100), kind="FOREST",
        trauma_score=BossService.BOSS_SPAWN_TRAUMA_THRESHOLD,
    )
    places = {}
    if with_lair:
        places["lair_1"] = PlaceState(place_id="lair_1", region_id="region_1", kind=PlaceKind.LAIR,
                                      position=(50.0, 50.0))
    return AuthoritativeState(
        tick=2000, seed=42, maturity=BossService.BOSS_SPAWN_THRESHOLD,
        regions={"region_1": region}, places=places, feature_flags=feature_flags or {},
    )


def _calamity_state(feature_flags=None):
    region = RegionState(id="badlands", name="Badlands", bounds=(50, 50, 60, 60), calamity_intensity=0.8)
    return AuthoritativeState(tick=5000, seed=42, regions={"badlands": region}, last_calamity_tick=0,
                              feature_flags=feature_flags or {})


def test_flag_is_registered_default_off() -> None:
    assert FeatureFlagManager()._flags[WORLD_BOSS_SPAWN_FLAG] is FeatureMode.OFF


@pytest.mark.parametrize("flags", [None, {}, {WORLD_BOSS_SPAWN_FLAG: "OFF"}, {WORLD_BOSS_SPAWN_FLAG: "SHADOW"}])
def test_only_an_explicit_on_enables_spawning(flags) -> None:
    assert world_boss_spawn_enabled(_gate_open_state(flags)) is False
    assert world_boss_spawn_enabled(_gate_open_state(ON)) is True


def test_region_boss_branch_is_inert_when_off_and_unchanged_when_on() -> None:
    gen = EntityGenerator(42)
    assert BossService.check_for_boss_spawn(_gate_open_state(), gen).entities_add == []
    on = BossService.check_for_boss_spawn(_gate_open_state(ON), gen)
    assert [e.kind for e in on.entities_add] == ["world_boss"]


def test_lair_branch_is_inert_when_off_and_unchanged_when_on() -> None:
    gen = EntityGenerator(42)
    assert BossService.check_for_lair_spawn(_gate_open_state(with_lair=True), gen).entities_add == []
    on = BossService.check_for_lair_spawn(_gate_open_state(ON, with_lair=True), gen)
    assert [e.kind for e in on.entities_add] == ["dragonkin"]


def test_calamity_boss_is_inert_when_off_but_the_trigger_still_advances() -> None:
    gen = EntityGenerator(42)
    off = CalamityService.process_world_dynamics(_calamity_state(), gen)
    assert not any(e.kind == "world_boss" for e in off.entities_add)
    assert off.last_calamity_tick_set == 5000  # the calamity cadence is unchanged
    on = CalamityService.process_world_dynamics(_calamity_state(ON), gen)
    assert any(e.kind == "world_boss" for e in on.entities_add)
    assert on.last_calamity_tick_set == 5000


def test_resolve_dynamics_spawns_no_boss_of_any_branch_when_off() -> None:
    gen = EntityGenerator(42)
    state = _gate_open_state(with_lair=True)
    refined = WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(), gen)
    assert not [e for e in refined.entities_add if e.kind in ("world_boss", "dragonkin")]
