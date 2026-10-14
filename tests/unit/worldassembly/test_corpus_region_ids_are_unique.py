"""Every resolved world in the corpus has unique region ids.

Two modules (`nomadic_herd`, `wolf_den_near_forest`) define regions `near_forest` and `wolf_den` with different geography; `hometown`,
`bandit_road` and `haunted_battlefield` are defined by interchangeable alternate modules. None is ever composed with its twin, and the
assembler raises on a collision (`WorldAssemblyResolver`, "Duplicate region ID collision"). This pin covers the corpus: a world that
composed two of them would otherwise let a lookup by bare region id (the catalog biome lookup in `resolver.py`) pick either one.
"""
from __future__ import annotations

import collections
from pathlib import Path

import pytest

from src.worldbuilding.repository import WorldRepository, WorldRepositoryError

WORLDS_DIR = Path(__file__).resolve().parents[3] / "data" / "worlds"
WORLDS = sorted(p.name for p in WORLDS_DIR.iterdir() if p.is_dir())
MIN_LOADED_SHARE = 0.8  # a repository API that breaks must not read as green because every case skipped


def _regions(world_id):
    spec, _context = WorldRepository(str(WORLDS_DIR)).load_world_with_context(world_id)
    return [region.id for region in spec.regions]


def test_most_worlds_load_so_the_per_world_cases_below_are_real():
    loaded = 0
    for world_id in WORLDS:
        try:
            _regions(world_id)
            loaded += 1
        except WorldRepositoryError:
            continue
    assert loaded >= MIN_LOADED_SHARE * len(WORLDS), f"only {loaded} of {len(WORLDS)} worlds load"


@pytest.mark.parametrize("world_id", WORLDS)
def test_a_resolved_world_has_unique_region_ids(world_id):
    try:
        ids = _regions(world_id)
    except WorldRepositoryError as error:  # a world that does not resolve is another test's finding; the guard above counts them
        pytest.skip(f"{world_id} does not load: {error}")
    counts = collections.Counter(ids)
    assert {rid: n for rid, n in counts.items() if n > 1} == {}
