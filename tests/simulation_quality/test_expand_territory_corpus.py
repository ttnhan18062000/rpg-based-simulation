"""Ideas 51/52 (Country EXPAND + population-driven expansion) corpus proof
(TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS) against the real `frontier_marches` world.

`EXPAND_TERRITORY` (src/engine/faction_constants.py) is gated by
`FactionDecisionPhase.execute()` (src/engine/faction_decision.py:174-189) on `mean_scarcity > 0.7`
over a faction's real `territory` plus a real faction-less adjacent region existing. Real,
empirically confirmed: every faction in `frontier_marches` compiles with EMPTY `territory` (no
region-ownership-to-faction-territory sync has happened yet at world-load time) -- this test hand-
seeds one faction's real `territory` tuple with a real, zero-resource-node region from the loaded
world (compute_regional_scarcity() returns 1.0 for any region with zero resource nodes, per its own
docstring), then calls the real, pure `FactionDecisionPhase.execute()` directly to prove the gate
and target-resolution logic both work correctly against real world data.
"""
from __future__ import annotations

from dataclasses import replace

from tools.calibrate_simq import _load_world_state
from src.engine.faction_constants import EXPAND_TERRITORY
from src.engine.faction_decision import FactionDecisionPhase


def _region_with_no_resource_nodes(state) -> str:
    for region in state.regions.values():
        xmin, ymin, xmax, ymax = region.bounds
        has_nodes = any(
            xmin <= px < xmax and ymin <= py < ymax
            for node in state.resource_nodes.values()
            for px, py in [node.position]
        )
        if not has_nodes:
            return region.id
    raise AssertionError("frontier_marches must have at least one resource-node-free region to seed scarcity=1.0")


def test_expand_territory_fires_for_highest_scarcity_faction_targeting_adjacent_unclaimed_region():
    state, report = _load_world_state("frontier_marches", seed=42)
    assert state is not None, "frontier_marches must be a real, compilable corpus world"
    assert state.factions, "frontier_marches must have real factions"

    scarce_region_id = _region_with_no_resource_nodes(state)
    faction_id = sorted(state.factions.keys())[0]
    seeded_faction = replace(state.factions[faction_id], territory=(scarce_region_id,))
    state = replace(state, factions={**state.factions, faction_id: seeded_faction})

    directives = FactionDecisionPhase.execute(state)

    expand_directives = [d for d in directives if d.faction_id == faction_id and d.directive_kind == EXPAND_TERRITORY]
    assert expand_directives, (
        f"faction {faction_id} with a real zero-resource (scarcity=1.0 > 0.7) territory region "
        f"must produce a real EXPAND_TERRITORY directive"
    )
    target_region_id = expand_directives[0].target_region
    assert target_region_id is not None
    assert target_region_id != scarce_region_id, "target must be a DIFFERENT region than the one already held"
    assert state.regions[target_region_id].owner_faction_id is None, (
        "EXPAND_TERRITORY's target must be a real, currently-unclaimed region"
    )
