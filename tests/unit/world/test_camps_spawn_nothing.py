"""A camp spawns nothing and raids nothing (owner ruling D70, TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70).

The camp used to add a monster every 30 ticks while it held fewer than max(2, maturity/10) members, and, past maturity 80 and a 500-tick
cooldown, conjured 3 + maturity raiders for a 20-maturity cost, all with no parent and no cost. Now a camp only matures; its members change by
death alone, until births (M1) or recruits.
"""
from __future__ import annotations

import dataclasses

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, CampState, PlaceKind, PlaceState, RegionState
from src.systems.world_systems.generator import EntityGenerator
from src.world.camp import CampService


def _goblin(eid, alive=True):
    return (V2EntityBuilder(eid).kind("goblin").location(50, 50)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE).combat(hp=10 if alive else 0).combat(alive=alive).build())


def _state(tick, *, maturity=10.0, members=1, last_raid_tick=0):
    return AuthoritativeState(
        tick=tick, seed=42,
        regions={"forest": RegionState(id="forest", name="Forest", kind="forest", bounds=(0, 0, 100, 100))},
        camps={"camp_1": CampState(id="camp_1", kind="goblin", position=(50, 50), maturity=maturity, last_raid_tick=last_raid_tick)},
        places={"town": PlaceState(place_id="town", region_id="forest", kind=PlaceKind.CITY, position=(10, 10))},
        entities={i: _goblin(i) for i in range(1, members + 1)}, next_entity_id=members + 1,
    )


def test_an_undersized_camp_adds_nothing_on_any_tick_of_a_long_run():
    adds = []
    for tick in range(0, 1500):
        adds += CampService.process_camps(_state(tick, members=1), EntityGenerator.for_state(_state(tick, members=1))).entities_add
    assert adds == []


def test_a_raid_ready_camp_adds_nothing_and_pays_nothing_on_any_tick():
    for tick in range(0, 1500, 7):
        upd = CampService.process_camps(_state(tick, maturity=95.0, last_raid_tick=-10_000), EntityGenerator(seed=42))
        assert upd.entities_add == [] and upd.camp_updates["camp_1"].last_raid_tick_set is None
        assert upd.camp_updates["camp_1"].maturity_delta > 0


def test_a_camps_members_only_fall_as_they_die():
    """Nothing refills the camp: dead members stay out of the count and the camp stays below its old cap."""
    state = _state(30, members=3)
    members = lambda s: sum(1 for e in s.entities.values() if e.combat.alive and e.kind == "goblin")
    assert members(state) == 3
    state = dataclasses.replace(state, entities={**state.entities, 2: _goblin(2, alive=False)})
    assert members(state) == 2
    assert CampService.process_camps(state, EntityGenerator.for_state(state)).entities_add == []
    assert members(state) == 2


def test_the_camp_service_names_no_spawner():
    import inspect
    src = inspect.getsource(CampService.process_camps)
    assert "spawn_monster" not in src and "spawn_raid" not in src


def test_a_camp_update_is_deterministic():
    a = CampService.process_camps(_state(500, maturity=95.0, last_raid_tick=-10_000), EntityGenerator(seed=42))
    b = CampService.process_camps(_state(500, maturity=95.0, last_raid_tick=-10_000), EntityGenerator(seed=42))
    assert a.camp_updates == b.camp_updates and a.entities_add == b.entities_add
