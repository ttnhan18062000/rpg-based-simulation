"""D57: a range-bound camp is not foodless by construction (module goblin_camp_forage and the pilot's camp edge).

Every composed world with a goblin camp has a food node inside the range its spawns keep to (``camp_food_gaps``). The wolf nests are
meat-only camps: berries do not satisfy them, so they are a REPORTED gap (prey placed in range is the hunting batch's work), never
filled with berries. A new gap fails here until it is fixed or named.
"""
import glob
import os

import pytest

from src.worldbuilding.camp_food import CAMP_SPAWN_RANGE, camp_food_gaps, camp_food_sources
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

WORLDS = "data/worlds"
# Meat-only camp kinds with no prey in range yet: reported, not filled with berries (the hunting batch places prey).
MEAT_ONLY_GAPS = {"wolf_den_nest", "calibration_wolf_nest"}


def _worlds():
    return sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(f"{WORLDS}/*/world.yaml"))


@pytest.mark.parametrize("world", _worlds())
def test_every_camp_has_a_food_way_in_range_except_the_named_meat_only_nests(world):
    spec, ctx = WorldRepository(WORLDS).load_world_with_context(world)
    state, _ = WorldCompiler.compile(spec, 42, context=ctx)
    assert set(camp_food_gaps(state)) <= MEAT_ONLY_GAPS


def test_the_goblin_camp_berries_lie_inside_the_smallest_spawn_leash():
    spec, ctx = WorldRepository(WORLDS).load_world_with_context("frontier_living_world")
    state, _ = WorldCompiler.compile(spec, 42, context=ctx)
    camp = state.camps["goblin_camp_place"]
    berries = [n for n in state.resource_nodes.values() if n.yields_item == "wild_berries" and n.remaining_charges > 0]
    assert any(abs(n.position[0] - camp.position[0]) + abs(n.position[1] - camp.position[1]) <= CAMP_SPAWN_RANGE for n in berries)


def test_the_report_names_the_land_that_supplies_each_camps_food():
    spec, ctx = WorldRepository(WORLDS).load_world_with_context("frontier_living_world")
    state, _ = WorldCompiler.compile(spec, 42, context=ctx)
    assert camp_food_sources(state) == {"goblin_camp_place": "goblin_camp_edge"}  # the wolf nest has none: a reported gap
