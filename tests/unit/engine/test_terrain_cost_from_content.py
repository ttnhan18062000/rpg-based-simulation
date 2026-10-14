"""D72 (owner ruling 2026-10-14): each terrain declares its move cost in content, code reads that and nothing else, and an unknown terrain is a content error
(TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1). Before D72 a hand-kept upper-case table meant lower-case content
terrain (`forest`, `swamp`, `mountain`, `road`) fell through to 1.0."""
from __future__ import annotations

import os

import pytest
from pydantic import ValidationError

from src.content.repository import CatalogRepository
from src.content.schema import TerrainDefinition
from src.engine import terrain_cost as tc
from src.engine.terrain_cost import UnknownTerrainError, configure_terrain_costs, reset_terrain_costs, terrain_cost, validate_terrain_ids
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.schema import InvalidWorldSpecError


@pytest.fixture(autouse=True)
def _fresh_costs():
    reset_terrain_costs()
    yield
    reset_terrain_costs()


RULED = {"plain": 1.0, "grass": 1.0, "forest": 1.5, "swamp": 3.0, "mountain": 4.0, "road": 0.5, "cave": 1.5, "ruin": 1.5, "river": 3.0}


@pytest.mark.parametrize("terrain_id,cost", sorted(RULED.items()))
def test_each_terrain_costs_what_the_ruling_declares_by_its_catalog_id(terrain_id, cost):
    assert terrain_cost(terrain_id) == cost


def test_a_river_stays_walkable_so_its_cost_is_finite_and_positive():
    assert 0 < terrain_cost("river") < float("inf")


def test_the_cost_field_is_required_so_a_terrain_without_one_does_not_load():
    with pytest.raises(ValidationError):
        TerrainDefinition(id="bog", display_name="Bog", hazard_multiplier=1.0)  # no move_cost_multiplier
    assert TerrainDefinition(id="bog", display_name="Bog", move_cost_multiplier=2.0).move_cost_multiplier == 2.0


def test_an_unknown_terrain_is_an_error_never_a_silent_1_0():
    with pytest.raises(UnknownTerrainError):
        terrain_cost("moon_dust")
    with pytest.raises(UnknownTerrainError):
        terrain_cost("FOREST")  # the match is exact: a tile carries a catalog id, no case folding in code
    with pytest.raises(UnknownTerrainError):
        validate_terrain_ids({"plain", "lava_field", "other_thing"})


def test_the_old_upper_case_table_is_gone():
    import src.core.state as state

    assert not hasattr(state, "TERRAIN_COST")


def test_the_compiler_fills_with_the_catalog_plain_and_every_tile_carries_a_catalog_id():
    assert tc.DEFAULT_TERRAIN_ID == "plain" and terrain_cost(tc.DEFAULT_TERRAIN_ID) == 1.0
    spec = WorldRepository("data/worlds").load_world("unit_faction_tension")
    state, _ = WorldCompiler.compile(spec, 42)
    assert set(state.terrain.values()) <= set(RULED) | {"snow", "volcanic"}
    assert "PLAIN" not in set(state.terrain.values())


def test_every_corpus_world_compiles_with_only_catalog_terrain():
    for world_id in sorted(os.listdir("data/worlds")):
        if not os.path.exists(f"data/worlds/{world_id}/world.yaml"):
            continue
        spec = WorldRepository("data/worlds").load_world(world_id)
        state, _ = WorldCompiler.compile(spec, 42)
        validate_terrain_ids(set(state.terrain.values()))


def test_a_terrain_the_catalog_does_not_declare_is_a_compile_time_content_error():
    spec = WorldRepository("data/worlds").load_world("unit_faction_tension")
    regions = [r.model_copy(update={"terrain": "lava_field"}) if i == 0 else r for i, r in enumerate(spec.regions)]
    with pytest.raises(InvalidWorldSpecError, match="lava_field"):
        WorldCompiler.compile(spec.model_copy(update={"regions": regions}), 42)


def test_a_movement_step_onto_forest_costs_what_forest_declares_and_a_road_costs_less():
    from dataclasses import replace

    from src.engine.rpg_depth import TerrainCostService
    from tests.helpers.scenario import compile_world

    state = compile_world("frontier_living_world", 42)
    forest = next(t for t, k in state.terrain.items() if k == "forest")
    road = next(t for t, k in state.terrain.items() if k == "road")
    assert TerrainCostService.get_tile_cost(forest, state) == 1.5
    assert TerrainCostService.get_tile_cost(road, state) == 0.5
    assert TerrainCostService.get_tile_cost(forest, replace(state, terrain={})) == 1.0  # a tile with no terrain recorded is the default terrain, plain


def test_two_catalogs_in_one_process_cannot_read_each_others_costs():
    """The cache holds content, never world state. A test catalog installed for one world is visible only until reset; the default content comes back
    unchanged, and a compile never writes a cost anywhere."""
    default_forest = terrain_cost("forest")
    other = CatalogRepository("data/content")
    other.load_all()
    other.terrain["forest"] = other.terrain["forest"].model_copy(update={"move_cost_multiplier": 9.0})
    configure_terrain_costs(other)
    assert terrain_cost("forest") == 9.0
    reset_terrain_costs()
    assert terrain_cost("forest") == default_forest == 1.5
    state, _ = WorldCompiler.compile(WorldRepository("data/worlds").load_world("unit_faction_tension"), 42)
    assert not hasattr(state, "terrain_costs")
    assert terrain_cost("forest") == 1.5
