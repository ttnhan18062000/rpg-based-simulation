"""LOC-08 refutation test 1 (consistency): a tile's terrain-owning region equals its lookup region.

Terrain paint and the runtime region lookup both read the resolved region-list order, highest precedence
first, so the region whose terrain a tile carries is the region the lookup returns for it, and therefore the
region whose hazard applies there. Before LOC-08 the painter let the last region win while the lookup let the
smallest-area region win, so they disagreed on every shared tile.
"""
from __future__ import annotations

import pytest

from src.core.region_resolution import resolve_region_among
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.schema import WorldSpec


def _spec(regions):
    return WorldSpec.model_validate({
        "schema_version": "worldspec.v1", "world_id": "precedence_probe", "name": "Precedence Probe",
        "topology": {"width": 60, "height": 60, "coordinate_system": "grid"},
        "regions": regions, "factions": [], "entities": [], "resources": [], "buildings": [],
    })


# road crossing a forest, a town nested in a forest, and an undeclared partial overlap (the scenarios LOC-08 owed)
REGIONS = [
    {"id": "town", "type": "town", "bounds": [10, 10, 20, 20], "terrain": "FLOOR"},        # nested in forest
    {"id": "road", "type": "road", "bounds": [0, 24, 59, 28], "terrain": "SAND"},          # crosses the forest
    {"id": "forest", "type": "wilderness", "bounds": [5, 5, 40, 40], "terrain": "FOREST"}, # container + crossed
    {"id": "marsh", "type": "wilderness", "bounds": [35, 35, 55, 55], "terrain": "SWAMP"}, # partial, undeclared
]


@pytest.fixture(scope="module")
def compiled():
    return WorldCompiler.compile(_spec(REGIONS), seed=42)[0]


def test_every_tile_terrain_matches_the_region_the_lookup_returns(compiled):
    flat = {"town": "FLOOR", "road": "SAND", "forest": "FOREST", "marsh": "SWAMP"}
    regions = list(compiled.regions.values())
    checked = 0
    for (x, y), terrain in compiled.terrain.items():
        owner = resolve_region_among(regions, x, y)
        if owner is None:
            continue
        assert terrain == flat[owner.id], f"({x},{y}): terrain {terrain} but lookup says {owner.id}"
        checked += 1
    assert checked > 500  # the overlaps were actually exercised


def test_the_expected_owners_in_the_three_scenarios(compiled):
    regions = list(compiled.regions.values())
    owner = lambda x, y: resolve_region_among(regions, x, y).id
    assert owner(15, 15) == "town"      # nested town beats its forest container
    assert owner(25, 26) == "road"      # the road crossing the forest owns its strip
    assert owner(25, 15) == "forest"    # forest ground outside both
    assert owner(37, 37) == "forest"    # undeclared partial overlap: earlier in resolved order (forest) wins
    assert owner(50, 50) == "marsh"
