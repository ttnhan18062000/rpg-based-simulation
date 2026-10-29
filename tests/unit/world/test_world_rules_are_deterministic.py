"""World rules give the same result for the same inputs: the calamity trigger, the seasonal escalation, camp placement; and every compiled entity has a valid role.

Sources: src/world/calamity.py (CalamityService.process_world_dynamics, CalamityPressurePropagator.propagate_seasonal),
src/worldbuilding/compiler.py (camps and entities), src/core/enums.py (EntityRole).
"""
from dataclasses import replace
from pathlib import Path

import pytest

from src.core.enums import EntityRole
from src.core.state import AuthoritativeState, RegionState
from src.systems.world_systems.generator import EntityGenerator
from src.world.calamity import CalamityPressurePropagator, CalamityService
from tests.helpers.scenario import compile_world


def _corpus_worlds():
    return sorted(p.name for p in Path("data/worlds").iterdir() if p.is_dir())


def _calamity_state():
    region = RegionState(id="badlands", name="Badlands", bounds=(50, 50, 60, 60), calamity_intensity=0.8)
    return AuthoritativeState(
        feature_flags={"ENABLE_WORLD_BOSS_SPAWN": "ON"}, tick=5000, seed=42, regions={"badlands": region}, last_calamity_tick=0
    )


def test_the_calamity_trigger_gives_the_same_result_for_the_same_inputs():
    first = CalamityService.process_world_dynamics(_calamity_state(), EntityGenerator(42))
    second = CalamityService.process_world_dynamics(_calamity_state(), EntityGenerator(42))

    assert first.entities_add and first.entities_add == second.entities_add
    assert first.last_calamity_tick_set == second.last_calamity_tick_set == 5000


def test_the_seasonal_escalation_gives_the_same_result_for_the_same_inputs():
    interval = CalamityPressurePropagator.SEASONAL_PROPAGATION_INTERVAL
    source = RegionState(id="A", name="A", bounds=(0, 0, 100, 100), calamity_intensity=0.4)
    neighbour = RegionState(id="B", name="B", bounds=(100, 0, 200, 100))
    state = AuthoritativeState(tick=interval, seed=42, regions={"A": source, "B": neighbour})

    first = CalamityPressurePropagator.propagate_seasonal(state)
    second = CalamityPressurePropagator.propagate_seasonal(replace(state))

    assert not first.is_noop()
    assert first.world_updates == second.world_updates


@pytest.mark.parametrize("world_id", _corpus_worlds())
def test_every_compiled_entity_has_a_valid_role(world_id):
    state = compile_world(world_id, 42)
    for entity in state.entities.values():
        assert isinstance(entity.identity.role, EntityRole), f"{world_id}: entity {entity.id} role {entity.identity.role!r}"


def _camp_positions(state):
    return {cid: camp.position for cid, camp in state.camps.items()}


@pytest.mark.parametrize("world_id", ["crowded_frontier", "frontier_living_world", "sandbox_world", "camp_maturity_calibration_pilot"])
def test_camp_placement_is_the_same_on_every_compile_whatever_the_seed(world_id):
    """Camps sit at authored place positions: two compiles with one seed, and a compile with another seed, place them identically."""
    first = _camp_positions(compile_world(world_id, 42))
    assert first, f"{world_id} has no camps"
    assert first == _camp_positions(compile_world(world_id, 42))
    assert first == _camp_positions(compile_world(world_id, 137))
