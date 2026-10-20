"""V3 pre-v1 step (designer ruling): a flight with no destination is not flight.

A subject whose panic resolves to its own tile (no region around it, no home) used to freeze in a PANIC_RETREAT hold, so a starving, wounded
merchant standing in reach of an inn never ate. Now the panic is not taken and the tick falls through the existing order (in-place survival,
then the arrival at a building). A real tactical hostile keeps the old freeze, so the fall-through never turns a held panic into a fight.
"""
from __future__ import annotations

from dataclasses import replace

from src.core.movement_modes import MovementMode
from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.engine.tactical import TacticalDecisionSystem
from tests.helpers.scenario import compile_world

MERCHANT, HUNTER = 37, 45
INN = (40.0, 31.0)


def _scene(merchant_at, hunter_at, hp=10):
    """Real frontier_living_world seed-42 merchant 37 (wounded, gold 0, hunger 100) with predator_hunter 45 beside it and a hunger project on the inn."""
    state = compile_world("frontier_living_world", 42)
    m, h = state.entities[MERCHANT], state.entities[HUNTER]
    m = replace(m, navigation=replace(m.navigation, position=merchant_at, movement_mode=MovementMode.REGROUP, target=INN),
                combat=replace(m.combat, hp=hp, max_hp=85), biological=replace(m.biological, hunger=100.0), inventory=replace(m.inventory, gold=0))
    h = replace(h, navigation=replace(h.navigation, position=hunter_at))
    obj = ObjectiveState(id="hunger_20003", kind=ObjectiveKind.REACH_LOCATION, target="20003", status=ObjectiveStatus.ACTIVE)
    proj = ProjectState(id="proj_hunger_1", kind="hunger", status=ProjectStatus.ACTIVE, objectives=[obj], active_objective_id=obj.id)
    m = replace(m, strategic=replace(m.strategic, projects={proj.id: proj}, current_project_id=proj.id, current_objective_id=obj.id))
    object.__setattr__(state, "entities", {MERCHANT: m, HUNTER: h})
    return state, m


def _decide(state, entity):
    return TacticalDecisionSystem.evaluate_entity_intent(state, entity)


def _action(update):
    return (update.task.payload_set or {}).get("action") if update.task else None


def _reason(update):
    return (update.task.payload_set or {}).get("reason") if update.task else None


def test_a_wounded_subject_in_unclaimed_space_beside_an_inn_eats_instead_of_holding_a_panic():
    state, merchant = _scene((41.0, 31.0), (41.0, 30.0), hp=10)  # (41,31) is in no region, merchant 37 has no home region
    update = _decide(state, merchant)
    assert _action(update) == "EAT" and update.task.payload_set["target_id"] == 20003


def test_a_wounded_subject_whose_retreat_has_a_real_destination_still_flees():
    state, merchant = _scene((30.0, 30.0), (30.0, 29.0), hp=10)  # inside the hometown region: an away vector exists
    update = _decide(state, merchant)
    assert _reason(update) == "PANIC_RETREAT"
    assert tuple(update.task.payload_set["target_position"]) != (30.0, 30.0)


def test_a_held_panic_beside_a_real_tactical_hostile_keeps_the_freeze_and_does_not_start_a_fight():
    """No regions in this state, so the panic has no destination; the adjacent monster is a hostile the tactical pass counts, so the old freeze stays."""
    from src.core.builder import V2EntityBuilder
    from src.core.enums import Faction
    from src.core.state import AuthoritativeState, BuildingState
    from src.engine.tactical import _has_tactical_hostiles

    hero = (V2EntityBuilder(1).kind("HERO").location(39.0, 31.0).identity(faction=Faction.HERO_GUILD)
            .combat(hp=7, max_hp=85, atk=10, def_stat=5, alive=True, readiness=100.0)
            .navigation(movement_mode=MovementMode.WANDER, target=INN).lifecycle(active=True).build())
    monster = (V2EntityBuilder(2).kind("MONSTER").location(39.0, 30.0).identity(faction=Faction.MONSTER_HORDE)
               .combat(hp=300, max_hp=300, atk=60, def_stat=5, alive=True, readiness=100.0)
               .navigation(movement_mode=MovementMode.WANDER).lifecycle(active=True).build())
    inn = BuildingState(id=20003, kind="inn", position=INN, functional=True)
    state = AuthoritativeState(tick=1, seed=1, entities={1: hero, 2: monster}, buildings={20003: inn}, blocked_tiles={(40, 31)}, building_tiles={}, terrain={})
    assert _has_tactical_hostiles(hero, [monster])
    update = _decide(state, hero)
    assert _reason(update) == "PANIC_RETREAT" and _action(update) != "ATTACK"
    assert tuple(update.task.payload_set["target_position"]) == (39.0, 31.0)  # still the hold
