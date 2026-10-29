"""Region-lookup properties no other test pins: a tie goes to the first region, the lookup is pure, and every region of every corpus world owns territory.

Sources: src/world/regions.py (RegionService.find_region_at), the compiled worlds under data/worlds.
"""
from pathlib import Path

import pytest

from src.core.state import AuthoritativeState, RegionState
from src.world.regions import RegionService
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository


def test_a_point_equidistant_from_two_centres_returns_the_first_region():
    r1 = RegionState(id="r1", name="R1", bounds=(0, 0, 10, 10))
    r2 = RegionState(id="r2", name="R2", bounds=(30, 0, 40, 10))
    # Neither region contains (20, 5); its distance to both centres (5, 5) and (35, 5) is 15.
    state = AuthoritativeState(tick=0, seed=42, regions={"r1": r1, "r2": r2})
    assert RegionService.find_region_at(state, (20, 5)).id == "r1"
    swapped = AuthoritativeState(tick=0, seed=42, regions={"r2": r2, "r1": r1})
    assert RegionService.find_region_at(swapped, (20, 5)).id == "r2"


def test_region_lookup_is_deterministic_over_a_grid_of_points():
    regions = {
        "a": RegionState(id="a", name="A", bounds=(0, 0, 40, 40)),
        "b": RegionState(id="b", name="B", bounds=(30, 30, 90, 90)),
        "c": RegionState(id="c", name="C", bounds=(100, 0, 140, 40)),
    }
    state = AuthoritativeState(tick=0, seed=42, regions=regions)
    points = [(x, y) for x in range(-20, 160, 7) for y in range(-20, 120, 7)]
    first = [RegionService.find_region_at(state, p).id for p in points]
    second = [RegionService.find_region_at(state, p).id for p in points]
    assert first == second


def _corpus_worlds():
    return sorted(p.name for p in Path("data/worlds").iterdir() if p.is_dir())


def _owns_a_tile(state, region):
    xmin, ymin, xmax, ymax = region.bounds
    return any(
        RegionService.find_region_at(state, (x, y)).id == region.id
        for x in range(xmin, xmax + 1)
        for y in range(ymin, ymax + 1)
    )


def test_the_ownership_check_can_fail_when_a_region_is_wholly_shadowed():
    """Positive control: two regions with identical bounds, the later one is shadowed by the first."""
    first = RegionState(id="first", name="First", bounds=(0, 0, 5, 5))
    shadowed = RegionState(id="shadowed", name="Shadowed", bounds=(0, 0, 5, 5))
    state = AuthoritativeState(tick=0, seed=42, regions={"first": first, "shadowed": shadowed})
    assert _owns_a_tile(state, first)
    assert not _owns_a_tile(state, shadowed)


@pytest.mark.parametrize("world_id", _corpus_worlds())
def test_every_region_of_a_corpus_world_owns_at_least_one_tile(world_id):
    """Overlap resolves to the first region, so a region could be wholly shadowed; none is."""
    state, _report = WorldCompiler.compile(WorldRepository("data/worlds").load_world(world_id), seed=42)
    for region in state.regions.values():
        assert _owns_a_tile(state, region), f"{world_id}: region {region.id} owns no tile of its own bounds"


def test_the_corpus_sweep_is_not_empty():
    counts = [
        len(WorldCompiler.compile(WorldRepository("data/worlds").load_world(w), seed=42)[0].regions)
        for w in _corpus_worlds()
    ]
    assert sum(counts) > 0 and max(counts) >= 2

