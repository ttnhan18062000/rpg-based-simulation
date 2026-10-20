"""D75 (MOV-04, divergence 2.125): terrain cost is TIME. A step onto a tile of cost N takes N ticks, the entity takes at most one step per
tick, and the readiness pre-check no longer reads the terrain factor."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState
from src.engine.legality import LegalityServiceV2
from src.engine.movement import MovementSystem

ROW = 10
GOAL = (60.0, float(ROW))


def _walker():
    return (V2EntityBuilder(1).kind("HERO").location(0.0, float(ROW)).identity(faction=Faction.HERO_GUILD)
            .combat(hp=100, max_hp=100, atk=10, def_stat=5, alive=True, readiness=100.0)
            .navigation(movement_mode=MovementMode.WANDER, target=GOAL).lifecycle(active=True).build())


def _state(entity, terrain_id, tick=0):
    terrain = {(x, ROW): terrain_id for x in range(0, 70)}
    return AuthoritativeState(tick=tick, seed=1, entities={entity.id: entity}, terrain=terrain)


def _walk(terrain_id, ticks):
    """The ticks on which a walker along a row of `terrain_id` takes a step."""
    entity = _walker()
    stepped = []
    for t in range(ticks):
        state = replace(_state(entity, terrain_id, tick=t), entities={1: entity})
        upd = MovementSystem.resolve_move(state, entity, GOAL, MovementMode.WANDER)[1]
        if upd.new_position is not None and tuple(upd.new_position) != tuple(entity.navigation.position):
            stepped.append(t)
            nav = replace(entity.navigation, position=tuple(upd.new_position),
                          step_ready_tick=upd.navigation.step_ready_tick_set)
            entity = replace(entity, navigation=nav)
    return stepped


def test_plain_takes_a_step_every_tick():
    assert _walk("plain", 12) == list(range(12))


def test_a_mountain_step_takes_four_ticks():
    assert _walk("mountain", 17) == [0, 4, 8, 12, 16]


def test_a_swamp_or_river_step_takes_three_ticks():
    assert _walk("swamp", 10) == [0, 3, 6, 9]
    assert _walk("river", 10) == [0, 3, 6, 9]


def test_a_forest_step_takes_one_and_a_half_ticks_on_average():
    # carried time: steps at 0, 2, 3, 5, 6, 8, ... (20 in 30 ticks, 1.5 ticks each; a flat two-tick step would give 15)
    assert _walk("forest", 9) == [0, 2, 3, 5, 6, 8]
    assert len(_walk("forest", 30)) == 20


def test_cave_and_ruin_take_the_forest_time():
    assert _walk("cave", 9) == _walk("forest", 9)
    assert _walk("ruin", 9) == _walk("forest", 9)


def test_a_road_is_no_faster_than_plain_under_one_step_per_tick():
    assert _walk("road", 12) == _walk("plain", 12) == list(range(12))


def test_a_held_tick_is_a_walk_not_a_failure():
    entity = _walker()
    state = _state(entity, "mountain", tick=0)
    upd = MovementSystem.resolve_move(state, entity, GOAL, MovementMode.WANDER)[1]
    entity = replace(entity, navigation=replace(entity.navigation, position=tuple(upd.new_position),
                                                step_ready_tick=upd.navigation.step_ready_tick_set))
    held = MovementSystem.resolve_move(replace(state, tick=2, entities={1: entity}), entity, GOAL, MovementMode.WANDER)[1]
    assert held.new_position is None
    assert held.navigation is None or (held.navigation.failure_reason is None and held.navigation.wait_count_delta == 0)


def test_the_pre_check_no_longer_reads_terrain():
    # readiness 15 covers the plain move cost (10) but not a mountain's old 4.0 multiple (40)
    entity = replace(_walker(), combat=replace(_walker().combat, readiness=15.0, move_cost=10.0))
    state = _state(entity, "mountain")
    ok, reason = LegalityServiceV2.verify_movement_legality(entity, (1.0, float(ROW)), state)
    assert ok, reason


def test_step_ready_tick_is_in_the_canonical_form_only_once_set():
    entity = _walker()
    assert "step_ready_tick" not in entity.to_canonical_dict()["navigation"]
    entity = replace(entity, navigation=replace(entity.navigation, step_ready_tick=4.0))
    assert entity.to_canonical_dict()["navigation"]["step_ready_tick"] == 4.0
