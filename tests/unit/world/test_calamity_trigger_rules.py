"""The calamity trigger is a pure tick rule: the minimum interval suppresses a spawn, only a forced-interval tick spawns, and tick 0 never does.

Source: src/world/calamity.py (CalamityService.process_world_dynamics, CALAMITY_MIN_INTERVAL 2000, CALAMITY_FORCE_INTERVAL 5000).
"""
from src.core.state import AuthoritativeState, RegionState
from src.systems.world_systems.generator import EntityGenerator
from src.world.calamity import CalamityService


def _process(tick, last_calamity_tick):
    region = RegionState(id="badlands", name="Badlands", bounds=(50, 50, 60, 60), calamity_intensity=0.8)
    state = AuthoritativeState(
        feature_flags={"ENABLE_WORLD_BOSS_SPAWN": "ON"}, tick=tick, seed=42, regions={"badlands": region}, last_calamity_tick=last_calamity_tick
    )
    return CalamityService.process_world_dynamics(state, EntityGenerator(42))


def test_a_forced_interval_tick_with_the_minimum_gap_spawns_and_advances_the_trigger():
    update = _process(5000, 0)
    assert [e.kind for e in update.entities_add] == ["world_boss"]
    assert update.last_calamity_tick_set == 5000


def test_a_forced_interval_tick_inside_the_minimum_gap_spawns_nothing():
    update = _process(5000, 5000 - CalamityService.CALAMITY_MIN_INTERVAL + 1)
    assert update.entities_add == [] and update.last_calamity_tick_set is None


def test_the_minimum_gap_exactly_met_spawns():
    update = _process(5000, 5000 - CalamityService.CALAMITY_MIN_INTERVAL)
    assert [e.kind for e in update.entities_add] == ["world_boss"]


def test_a_tick_that_is_not_a_forced_interval_spawns_nothing_however_old_the_last_calamity():
    for tick in (2000, 4999, 5001, 7500):
        update = _process(tick, 0)
        assert update.entities_add == [] and update.last_calamity_tick_set is None, tick


def test_tick_zero_never_spawns():
    update = _process(0, -CalamityService.CALAMITY_FORCE_INTERVAL)
    assert update.entities_add == [] and update.last_calamity_tick_set is None
