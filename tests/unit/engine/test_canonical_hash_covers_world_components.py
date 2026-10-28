"""The canonical state hash (the one the kernel's final proof digest and every replay comparison use) changes when any world component changes.

Path: Kernel final digest -> CanonicalHashScheduler.compute_digest -> CanonicalStateHasher.get_hash (src/engine/checkpoint.py). The lighter
src/replay/fingerprint.py::StateFingerprinter is NOT this hash: it omits buildings and camps and guards phase isolation inside a tick.
"""
from dataclasses import replace

import pytest

from src.core.state import AuthoritativeState, BuildingState, CampState, RegionState, ResourceNodeState
from src.engine.checkpoint import CanonicalHashScheduler, CanonicalStateHasher
from src.systems.world_systems.generator import EntityGenerator


def _base():
    return AuthoritativeState(
        tick=10,
        seed=42,
        regions={"r": RegionState(id="r", name="R", bounds=(0, 0, 10, 10))},
        buildings={1: BuildingState(id=1, kind="shop", position=(1.0, 1.0))},
        camps={"c": CampState(id="c", kind="goblin_camp", position=(2.0, 2.0))},
        resource_nodes={5: ResourceNodeState(id=5, kind="tree", position=(3.0, 3.0), yields_item="wood", remaining_charges=3, max_charges=3, required_ticks=2)},
        global_resources={"gold": 10},
        last_calamity_tick=0,
    )


def _changes():
    base = _base()
    return {
        "resource node": replace(base, resource_nodes={5: replace(base.resource_nodes[5], remaining_charges=2)}),
        "building": replace(base, buildings={1: replace(base.buildings[1], hp=base.buildings[1].hp - 50)}),
        "region": replace(base, regions={"r": replace(base.regions["r"], hazard_level=0.5)}),
        "camp": replace(base, camps={"c": replace(base.camps["c"], maturity=0.5)}),
        "calamity tick": replace(base, last_calamity_tick=5000),
        "global resource": replace(base, global_resources={"gold": 11}),
    }


def test_the_same_state_hashes_the_same():
    assert CanonicalStateHasher.get_hash(_base()) == CanonicalStateHasher.get_hash(_base())


@pytest.mark.parametrize("component", sorted(_changes()))
def test_a_change_to_each_world_component_changes_the_canonical_hash(component):
    assert CanonicalStateHasher.get_hash(_changes()[component]) != CanonicalStateHasher.get_hash(_base())


def test_the_kernel_final_digest_is_the_canonical_hash():
    state = _base()
    digest = CanonicalHashScheduler(state.tick).compute_digest(state, state.tick).require_value()
    assert digest == CanonicalStateHasher.get_hash(state)


def test_a_spawned_world_boss_changes_the_canonical_hash_and_so_does_wounding_it():
    base = _base()
    boss = EntityGenerator(42).spawn_monster(pos=(5.0, 5.0), kind="world_boss", difficulty_tier=4)
    with_boss = replace(base, entities={boss.id: boss})
    assert CanonicalStateHasher.get_hash(with_boss) != CanonicalStateHasher.get_hash(base)

    wounded = replace(boss, combat=replace(boss.combat, hp=boss.combat.hp - 10))
    assert CanonicalStateHasher.get_hash(replace(base, entities={boss.id: wounded})) != CanonicalStateHasher.get_hash(with_boss)
