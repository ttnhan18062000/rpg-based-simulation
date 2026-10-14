"""D75 completion: a position swap and a yield displacement pay the step time of the tile the entity is moved onto, and an entity still
taking its previous step (`step_ready_tick`) is neither swapped nor displaced. Before, only the entity's own step (`resolve_move`) paid."""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction, ReasonCode
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.engine.movement import MovementSystem
from tests.integration.pipeline.test_movement_micro_arena_position_swap import (
    make_actor, make_state, move_intent, one_tile_corridor_walls, refine_and_apply)

TICK = 10


def _corridor(terrain_id):
    walls = one_tile_corridor_walls()
    return {**walls, (0, 0): terrain_id, (1, 0): terrain_id}


def _swap_state(terrain_id, a_ready=0.0, b_ready=0.0):
    a = make_actor(1, (0.0, 0.0))
    b = make_actor(2, (1.0, 0.0))
    a = replace(a, navigation=replace(a.navigation, step_ready_tick=a_ready))
    b = replace(b, navigation=replace(b.navigation, step_ready_tick=b_ready))
    return make_state(entities={1: a, 2: b}, terrain=_corridor(terrain_id), tick=TICK)


def _swap(state):
    return refine_and_apply(state, StateUpdate(entity_updates={1: move_intent(1, (1.0, 0.0)), 2: move_intent(2, (0.0, 0.0))}))


def test_a_swap_onto_a_mountain_costs_both_four_ticks():
    _, after = _swap(_swap_state("mountain"))
    assert after.entities[1].navigation.position == (1.0, 0.0) and after.entities[2].navigation.position == (0.0, 0.0)
    assert after.entities[1].navigation.step_ready_tick == TICK + 4.0
    assert after.entities[2].navigation.step_ready_tick == TICK + 4.0


def test_a_swap_onto_plain_costs_one_tick():
    _, after = _swap(_swap_state("plain"))
    assert after.entities[1].navigation.step_ready_tick == TICK + 1.0


def test_an_entity_still_taking_its_step_is_not_swapped():
    state = _swap_state("plain", a_ready=TICK + 2.0)
    _, after = _swap(state)
    assert after.entities[1].navigation.position == (0.0, 0.0)
    assert after.entities[2].navigation.position == (1.0, 0.0)


def _yield_state(terrain, occupant_ready=0.0):
    hero = (V2EntityBuilder(1).kind("actor").location(1.0, 1.0).identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
            .combat(hp=100, max_hp=100, alive=True, readiness=100.0).navigation(movement_mode=MovementMode.WANDER).build())
    monster = (V2EntityBuilder(2).kind("actor").location(2.0, 1.0).identity(role=EntityRole.MONSTER, faction=Faction.HERO_GUILD)
               .combat(hp=100, max_hp=100, alive=True, readiness=100.0).navigation(movement_mode=MovementMode.WANDER).build())
    monster = replace(monster, navigation=replace(monster.navigation, step_ready_tick=occupant_ready))
    s1 = V2EntityBuilder(3).kind("actor").location(1.0, 0.0).identity(role=EntityRole.MONSTER, faction=Faction.HERO_GUILD).combat(hp=100, max_hp=100, alive=True).build()
    s2 = V2EntityBuilder(4).kind("actor").location(1.0, 2.0).identity(role=EntityRole.MONSTER, faction=Faction.HERO_GUILD).combat(hp=100, max_hp=100, alive=True).build()
    return AuthoritativeState(tick=TICK, seed=42, entities={1: hero, 2: monster, 3: s1, 4: s2}, terrain=terrain), hero


def test_a_yielding_occupant_pays_the_step_time_of_the_tile_it_is_moved_onto():
    terrain = {(x, y): "swamp" for x in range(-1, 5) for y in range(-1, 4)}
    state, hero = _yield_state(terrain)
    updates = MovementSystem.resolve_move(state, hero, (2.0, 1.0))
    assert updates[2].navigation.failure_reason == ReasonCode.YIELDING
    assert updates[2].navigation.step_ready_tick_set == TICK + 3.0


def test_an_occupant_still_taking_its_step_is_not_displaced():
    state, hero = _yield_state({}, occupant_ready=TICK + 2.0)
    updates = MovementSystem.resolve_move(state, hero, (2.0, 1.0))
    assert 2 not in updates or updates[2].new_position is None
