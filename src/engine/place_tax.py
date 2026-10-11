"""The tax on a sale or a wage (EXCH-02, owner decision 51 and 58): a declared share, rounded down per transaction, paid out of the
receiver's proceeds to the treasury of the faction that holds the place the building stands in. Nothing is taxed that is not income: no
periodic levy exists, and a subject that earns and sells nothing pays nothing."""
from __future__ import annotations

from typing import Any, Optional, Tuple

from src.content_semantics.faction import get_faction_semantics_service
from src.core.treasury import neutral_faction
from src.engine.spatial_query import SpatialQueryService


def tax_on(state: Any, building: Any, amount: int) -> Tuple[Optional[int], int]:
    """(faction, tax) for `amount` of income received at `building`: the faction holding the building's region and the share it is due,
    rounded down to whole coin (exact integer arithmetic on the declared share, so 0.1 of 30 is 3, never 2.99); (None, 0) when nobody holds the
    place or the region declares no share."""
    region = SpatialQueryService.get_building_region(state, building.id)
    if region is None or region.owner_faction_id is None or region.tax_share <= 0 or amount <= 0:
        return None, 0
    micro = round(region.tax_share * 1_000_000)
    return int(region.owner_faction_id), (int(amount) * micro) // 1_000_000


def building_holder(state: Any, building: Any) -> Optional[int]:
    """The faction whose ground `building` stands on, or None where nobody holds it."""
    region = SpatialQueryService.get_building_region(state, building.id)
    return int(region.owner_faction_id) if region is not None and region.owner_faction_id is not None else None


def _holder_or_neutral(region: Any) -> int:
    """The faction holding `region`, else the neutral treasury's bucket."""
    return int(region.owner_faction_id) if region is not None and region.owner_faction_id is not None else neutral_faction()


def reward_payer(state: Any, source_building_id: Optional[int] = None) -> Optional[int]:
    """The treasury that funds a quest reward (EXCH-02, decisions 38 and 58, ruling 61): the faction holding the ground of the building the quest
    was posted at, the one real giver. None where there is no giver (the quest was posted nowhere, or on ground nobody holds): that quest pays
    no coin and no item, only experience. A reward is never minted and never paid by a stranger."""
    if source_building_id is None or source_building_id not in state.buildings:
        return None
    region = SpatialQueryService.get_building_region(state, source_building_id)
    return int(region.owner_faction_id) if region is not None and region.owner_faction_id is not None else None


def offering_faction_payer(faction_source: Optional[str]) -> Optional[int]:
    """The treasury of the faction that posted a quest opportunity (its legacy bucket), or None for a world event with no giver."""
    if not faction_source:
        return None
    return int(get_faction_semantics_service().get_legacy_faction_bucket(faction_source))


def ground_holder(state: Any, entity: Any) -> int:
    """The faction whose treasury receives what is taken from `entity` where it stands (the neutral treasury where nobody holds the ground)."""
    return _holder_or_neutral(SpatialQueryService.get_region_at(state, entity.navigation.position))
