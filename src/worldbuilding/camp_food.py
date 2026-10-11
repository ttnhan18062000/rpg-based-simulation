"""A range-bound camp is not foodless by construction (owner decision D57, designer's range rule).

A camp's spawns are placed at the camp position and keep to a leash around it (``generator.py``: 8 to 10 tiles). A subject judges its
ways to eat inside its range (``LeashService.way_in_range``), so a camp with no food node within that range has no way for its
spawns to eat at all. ``camp_food_gaps`` names those camps; the corpus test holds every composed world to it.
"""
from __future__ import annotations

from typing import Dict, List

from src.core.items import food_hunger_recovery
from src.core.region_resolution import resolve_region_among
from src.core.state import AuthoritativeState

# The smallest leash a camp spawn gets (the goblin, ``generator.py``); a node within it is in range of every spawn kind.
CAMP_SPAWN_RANGE = 8.0


def camp_food_gaps(state: AuthoritativeState) -> List[str]:
    """Ids of the camps that have no food node with charges inside the range their spawns keep to."""
    food_nodes = [n for n in state.resource_nodes.values() if n.remaining_charges > 0 and food_hunger_recovery(n.yields_item) > 0.0]
    gaps: List[str] = []
    for camp_id, camp in state.camps.items():
        cx, cy = camp.position
        if not any(abs(n.position[0] - cx) + abs(n.position[1] - cy) <= CAMP_SPAWN_RANGE for n in food_nodes):
            gaps.append(camp_id)
    return sorted(gaps)


def camp_food_sources(state: AuthoritativeState) -> Dict[str, str]:
    """For each camp with a food way in range, the id of the region (the land) that supplies the nearest one.

    The designer's rule: a camp's food is its own land's wild food, the amount from that land's fertility. This names the land, so a
    report can say which region supplied the way."""
    sources: Dict[str, str] = {}
    for camp_id, camp in state.camps.items():
        cx, cy = camp.position
        in_range = [n for n in state.resource_nodes.values()
                    if n.remaining_charges > 0 and food_hunger_recovery(n.yields_item) > 0.0
                    and abs(n.position[0] - cx) + abs(n.position[1] - cy) <= CAMP_SPAWN_RANGE]
        if not in_range:
            continue
        nearest = min(in_range, key=lambda n: (abs(n.position[0] - cx) + abs(n.position[1] - cy), n.id))
        region = resolve_region_among(state.regions.values(), nearest.position[0], nearest.position[1])
        sources[camp_id] = region.id if region is not None else "unowned"
    return sources
