"""Rule ENV-07 at the two regional-trauma producers: the death block in WorldDynamicsSystem and the
building-destruction increment in ApplyPlan (owner decision 15)."""
from __future__ import annotations

from dataclasses import replace

from src.core.state import AuthoritativeState, RegionState
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.engine.world_dynamics import WorldDynamicsSystem
from src.systems.world_systems.generator import EntityGenerator
from tests.helpers.scenario import compile_world, DEFAULT_SEED


def _trauma_delta_for_death(outcome_kind: str, attacker_id=None, hazard_damage=0) -> float:
    """Run the real death block on the first live entity of a compiled world with one fatal update."""
    state = compile_world("frontier_living_world", DEFAULT_SEED)
    region = next(iter(state.regions.values()))
    entity = next(e for e in state.entities.values() if e.combat.alive and e.lifecycle.active)
    x0, y0, x1, y1 = region.bounds
    nav = replace(entity.navigation, position=((x0 + x1) // 2, (y0 + y1) // 2))
    entity = replace(entity, navigation=nav)
    # only the resolved region's id matters, so put every region at trauma 0 and read the delta
    state = replace(state, entities={**state.entities, entity.id: entity})
    update = StateUpdate(entity_updates={entity.id: EntityUpdate(
        entity_id=entity.id,
        combat=CombatUpdate(alive_set=False, outcome_kind=outcome_kind,
                            attacker_id=attacker_id, hazard_damage=hazard_damage))})
    refined = WorldDynamicsSystem.resolve_dynamics(state, update, EntityGenerator(DEFAULT_SEED))
    return sum(w.trauma_delta for w in refined.world_updates.values())


def test_a_defeat_adds_one_trauma() -> None:
    assert _trauma_delta_for_death("DEFEAT", attacker_id=1) == 1.0


def test_a_kill_adds_one_trauma() -> None:
    assert _trauma_delta_for_death("KILL", attacker_id=1) == 1.0


def test_a_hazard_death_adds_no_trauma() -> None:
    assert _trauma_delta_for_death("HAZARD", hazard_damage=30) == 0.0


def test_the_rule_is_the_cause_not_the_presence_of_an_attacker() -> None:
    """A HAZARD-decided death that still carries an attacker id (it was hit earlier) is judged by
    its recorded cause, not by 'has a killer'; the reverse holds for a violent death with none."""
    assert _trauma_delta_for_death("HAZARD", attacker_id=7, hazard_damage=30) == 0.0
    assert _trauma_delta_for_death("DEFEAT", attacker_id=None) == 1.0


def _building_trauma(hp: int, hp_delta: int) -> float:
    from src.core.state import BuildingState
    from src.core.updates import BuildingUpdate
    from src.engine.apply import ApplyPath

    region = RegionState(id="town", name="Town", bounds=(0, 0, 50, 50))
    building = BuildingState(id=1, kind="SHOP", position=(10.0, 10.0), hp=hp, max_hp=500, functional=True)
    state = AuthoritativeState(tick=1, seed=1, regions={"town": region}, buildings={1: building})
    update = StateUpdate(building_updates={1: BuildingUpdate(building_id=1, hp_delta=hp_delta)})
    new_state = ApplyPath.apply_generation(state, update)
    return new_state.regions["town"].trauma_score


def test_a_sabotaged_building_destroyed_adds_two_trauma() -> None:
    assert abs(_building_trauma(hp=40, hp_delta=-50) - 2.0) < 0.01


def test_a_destruction_without_a_damaging_delta_adds_no_trauma() -> None:
    """Not violent by cause: a functional building already at 0 hp with no damage this tick."""
    assert _building_trauma(hp=0, hp_delta=0) < 0.01
