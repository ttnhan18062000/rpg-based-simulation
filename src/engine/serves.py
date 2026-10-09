"""Who a building serves or hires (owner decision 43).

Money, wages and trade are people-only rules: a subject takes part only if its species is authored with the ``keeps_coin_and_trades`` trait. A
place also serves or hires a subject only while the faction that controls it is not hostile to the subject: the controlling faction is the owner
of the region at the building's tile (``RegionState.owner_faction_id``, the legacy faction bucket, so "a town does not serve a hostile raider"
is only as fine as that bucket); a region with no owner serves anyone with the trait. One helper for the sale, the shift and the inn route.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional

from src.content_semantics.faction import (
    get_faction_id_str,
    get_faction_semantics_service,
)
from src.core.enums import Faction
from src.engine.spatial_query import SpatialQueryService

TRADES_TRAIT = "keeps_coin_and_trades"


def keeps_coin(entity: Any) -> bool:
    """True when the entity's species is authored with the coin-and-trade trait."""
    species_id = (entity.identity.properties or {}).get("species_id")
    species = get_faction_semantics_service().repo.get_species(species_id) if species_id else None
    return species is not None and TRADES_TRAIT in species.natural_traits


def _controlling_faction(state: Any, building: Any) -> Optional[str]:
    region = SpatialQueryService.get_region_at(state, building.position)
    owner = None if region is None else region.owner_faction_id
    if owner is None:
        return None
    try:
        return Faction(owner).name.lower()
    except ValueError:
        return None


def serves(state: Any, subject: Any, building: Any) -> bool:
    """True when `building` serves or hires `subject`: it keeps coin and trades, and the building's controlling faction is not hostile to it."""
    if not keeps_coin(subject):
        return False
    controller = _controlling_faction(state, building)
    return controller is None or not get_faction_semantics_service().is_hostile_compat(get_faction_id_str(subject), controller)


def nearest_serving(state: Any, subject: Any, buildings: Iterable[Any], kind: str, accept: Any = None) -> Optional[Any]:
    """The nearest functional building of `kind` that serves `subject` (and passes `accept`, when given); ties keep the lower id."""
    px, py = subject.navigation.position
    best, best_key = None, None
    for building in buildings:
        if building.kind != kind or not building.functional or (accept is not None and not accept(building)) or not serves(state, subject, building):
            continue
        key = (abs(building.position[0] - px) + abs(building.position[1] - py), building.id)
        if best_key is None or key < best_key:
            best, best_key = building, key
    return best
