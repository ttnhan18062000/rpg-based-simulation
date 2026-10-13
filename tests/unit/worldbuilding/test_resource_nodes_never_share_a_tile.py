"""LAW-SPAWN-OCCUPANCY at world creation: no two resource nodes stand on one tile (plant cover adds many nodes to a region, owner row 59).

Found by the combined sweep: frontier_extended at seed 123 placed a herb patch and a cover patch (and two cover patches) on the same tile, and the kernel
raised HardLawViolation at initial placement. The compiler now skips a draw on a tile a node already stands on; a draw that does not collide is unchanged."""
from __future__ import annotations

from collections import Counter

import pytest

from tests.helpers.scenario import compile_world

pytestmark = [pytest.mark.domain("world"), pytest.mark.level("unit")]

WORLDS = ("frontier_extended", "frontier_living_world", "swamp_border_world", "frontier_marches", "wilderness_survival", "sandbox_world")
SEEDS = (42, 43, 44, 123)


@pytest.mark.parametrize("world", WORLDS)
@pytest.mark.parametrize("seed", SEEDS)
def test_no_two_resource_nodes_share_a_tile(world, seed):
    state = compile_world(world, seed)
    shared = {tile: n for tile, n in Counter((int(node.position[0]), int(node.position[1])) for node in state.resource_nodes.values()).items() if n > 1}
    assert not shared, f"{world} seed {seed}: nodes share tiles {shared}"
