"""Each terrain declares in content whether it gives cover and whether it is high ground; the combat checks read that and name no terrain
(TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT, designer application of D33/D56/D72). Before it, the checks named upper-case WALL, FOREST,
MOUNTAIN and HILL, so on lower-case catalog terrain neither ever fired."""
from __future__ import annotations

import inspect

import pytest
from pydantic import ValidationError

from src.content import terrain_cost as tc
from src.content.schema import TerrainDefinition
from src.content.terrain_cost import UnknownTerrainError, reset_terrain_costs, terrain_gives_cover, terrain_is_high_ground
from src.core.state import AuthoritativeState
from src.engine.legality import LegalityServiceV2


@pytest.fixture(autouse=True)
def _fresh_terrain():
    reset_terrain_costs()
    yield
    reset_terrain_costs()


COVER = {"forest", "mountain", "ruin", "cave"}
HIGH = {"mountain"}
ALL = ["plain", "grass", "forest", "swamp", "cave", "mountain", "ruin", "road", "snow", "volcanic", "river"]


@pytest.mark.parametrize("terrain_id", ALL)
def test_each_terrain_declares_the_ruled_cover_and_high_ground_by_catalog_id(terrain_id):
    assert terrain_gives_cover(terrain_id) is (terrain_id in COVER)
    assert terrain_is_high_ground(terrain_id) is (terrain_id in HIGH)


def test_the_whole_catalog_is_covered_by_the_ruling():
    assert sorted(tc._terrain()) == sorted(ALL)


@pytest.mark.parametrize("missing", ["gives_cover", "high_ground"])
def test_a_terrain_that_does_not_declare_both_flags_does_not_load(missing):
    fields = {"id": "bog", "display_name": "Bog", "move_cost_multiplier": 2.0, "gives_cover": False, "high_ground": False}
    del fields[missing]
    with pytest.raises(ValidationError):
        TerrainDefinition(**fields)


def test_an_unknown_terrain_is_an_error_not_no_cover():
    with pytest.raises(UnknownTerrainError):
        terrain_gives_cover("FOREST")  # exact catalog ids only: no case folding in code
    with pytest.raises(UnknownTerrainError):
        terrain_is_high_ground("HILL")


def _state(terrain):
    return AuthoritativeState(tick=1, seed=42, entities={}, terrain=terrain)


def test_a_defender_with_forest_behind_it_has_cover_from_a_distant_attacker():
    state = _state({(5, 5): "plain", (4, 5): "forest"})  # attacker to the west at x=0: the tile behind the defender, on the attacker's side
    assert LegalityServiceV2.check_cover((0.0, 5.0), (5.0, 5.0), state) is True


@pytest.mark.parametrize("terrain_id", sorted(COVER))
def test_every_cover_terrain_gives_cover_and_the_others_do_not(terrain_id):
    assert LegalityServiceV2.check_cover((0.0, 5.0), (5.0, 5.0), _state({(4, 5): terrain_id})) is True


@pytest.mark.parametrize("terrain_id", sorted(set(ALL) - COVER))
def test_a_terrain_that_declares_no_cover_gives_none(terrain_id):
    assert LegalityServiceV2.check_cover((0.0, 5.0), (5.0, 5.0), _state({(4, 5): terrain_id})) is False


def test_no_tile_behind_the_defender_is_no_cover_and_an_adjacent_attacker_gets_none():
    assert LegalityServiceV2.check_cover((0.0, 5.0), (5.0, 5.0), _state({})) is False
    assert LegalityServiceV2.check_cover((4.0, 5.0), (5.0, 5.0), _state({(4, 5): "forest"})) is False


def test_cover_is_read_on_the_vertical_axis_too():
    state = _state({(5, 4): "ruin"})
    assert LegalityServiceV2.check_cover((5.0, 0.0), (5.0, 5.0), state) is True


def test_high_ground_is_the_attacker_on_mountain_against_a_defender_who_is_not():
    assert LegalityServiceV2.check_high_ground((1.0, 1.0), (1.0, 2.0), _state({(1, 1): "mountain", (1, 2): "plain"})) is True
    assert LegalityServiceV2.check_high_ground((1.0, 1.0), (1.0, 2.0), _state({(1, 1): "mountain", (1, 2): "mountain"})) is False
    assert LegalityServiceV2.check_high_ground((1.0, 1.0), (1.0, 2.0), _state({(1, 1): "forest", (1, 2): "plain"})) is False
    assert LegalityServiceV2.check_high_ground((1.0, 1.0), (1.0, 2.0), _state({})) is False


def test_the_two_checks_name_no_terrain():
    for check in (LegalityServiceV2.check_cover, LegalityServiceV2.check_high_ground):
        source = inspect.getsource(check)
        for name in ("WALL", "HILL", "FOREST", "MOUNTAIN", "PLAIN", "forest", "mountain"):
            assert f'"{name}"' not in source, f"{check.__name__} still names {name}"
