"""A chokepoint is a one-tile gap between two blocked tiles (the tiles structures occupy), never between terrain tiles
(TCK-20261014-CHOKEPOINTS-ARE-FOUND-FROM-BLOCKED-TILES, designer application of D56). Before it, detection named the terrain "WALL", which
no catalog terrain is, so no chokepoint had ever been found."""
from __future__ import annotations

import inspect
from dataclasses import replace

import pytest

from src.engine.positioning import PositioningService
from tests.helpers.scenario import compile_world, empty_inventories

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
ENTITY = 2


def _state(blocked, terrain=None):
    state = empty_inventories(compile_world(WORLD_ID))
    object.__setattr__(state, "blocked_tiles", set(blocked))
    if terrain is not None:
        object.__setattr__(state, "terrain", dict(terrain))
    return state


def _at(entity, pos):
    return replace(entity, navigation=replace(entity.navigation, position=pos))


def _found(state, pos=(10.0, 10.0), radius=8):
    return PositioningService.identify_chokepoints(_at(state.entities[ENTITY], pos), state, radius)


def test_a_one_tile_gap_between_two_blocked_tiles_side_by_side_is_a_chokepoint():
    assert (10.0, 10.0) in _found(_state({(9, 10), (11, 10)}))


def test_a_one_tile_gap_between_two_blocked_tiles_above_and_below_is_a_chokepoint():
    assert (10.0, 10.0) in _found(_state({(10, 9), (10, 11)}))


def test_a_gap_between_open_terrain_tiles_is_not_a_chokepoint():
    terrain = {(9, 10): "forest", (11, 10): "mountain", (10, 9): "ruin", (10, 11): "cave"}
    assert _found(_state(set(), terrain)) == []


def test_a_terrain_called_wall_is_not_a_wall_only_a_blocked_tile_is():
    assert _found(_state(set(), {(9, 10): "WALL", (11, 10): "WALL"})) == []


def test_a_blocked_tile_is_never_itself_a_chokepoint():
    # (10, 10) is blocked and has blocked neighbours on both sides: it is not a walkable gap.
    assert (10.0, 10.0) not in _found(_state({(9, 10), (10, 10), (11, 10)}))


def test_a_single_blocked_tile_or_two_that_are_not_opposite_make_no_chokepoint():
    assert _found(_state({(9, 10)})) == []
    assert _found(_state({(9, 10), (10, 11)})) == []


def test_only_tiles_within_the_radius_are_considered():
    state = _state({(29, 30), (31, 30)})
    assert _found(state, pos=(10.0, 10.0), radius=8) == []
    assert (30.0, 30.0) in _found(state, pos=(30.0, 30.0), radius=8)


def test_the_detection_names_no_terrain():
    source = inspect.getsource(PositioningService.identify_chokepoints)
    assert "WALL" not in source and "terrain" not in source.replace("terrain name", "")
