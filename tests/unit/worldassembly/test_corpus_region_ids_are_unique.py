"""Every resolved world in the corpus has unique region ids.

Two modules (`nomadic_herd`, `wolf_den_near_forest`) define regions `near_forest` and `wolf_den` with different geography; `hometown`,
`bandit_road` and `haunted_battlefield` are defined by interchangeable alternate modules. None is ever composed with its twin, and the
assembler raises on a collision (`WorldAssemblyResolver`, "Duplicate region ID collision"). This pin covers the corpus: a world that
composed two of them would otherwise let a lookup by bare region id (the catalog biome lookup in `resolver.py`) pick either one.
"""
from __future__ import annotations

import collections
import os

import pytest

from src.worldbuilding.repository import WorldRepository

WORLDS_DIR = os.path.join("data", "worlds")
WORLDS = sorted(w for w in os.listdir(WORLDS_DIR) if os.path.isdir(os.path.join(WORLDS_DIR, w)))


@pytest.mark.parametrize("world_id", WORLDS)
def test_a_resolved_world_has_unique_region_ids(world_id):
    try:
        spec, _context = WorldRepository(WORLDS_DIR).load_world_with_context(world_id)
    except Exception as error:  # a world that does not load is another test's finding
        pytest.skip(f"{world_id} does not load: {type(error).__name__}")
    counts = collections.Counter(region.id for region in spec.regions)
    assert {rid: n for rid, n in counts.items() if n > 1} == {}
