"""What a dead body leaves to eat (decision 44): raw meat sized by the body's kind, declared in content.

A body is a body: any death leaves its meat, whatever the cause. The meat is a typed source in the conservation ledger
(`MEAT_FROM_BODY`) and a sink when a corpse is cleaned up with meat still on it (`MEAT_DECAYED`).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List

from src.content_semantics.faction import get_species_id_str
from src.core.models.inventory import ItemStack
from src.engine.behavior_consumers import get_kind_properties

if TYPE_CHECKING:
    from src.core.state import EntityState

RAW_MEAT_ITEM = "raw_meat"
# Typed ledger kinds (Bible 03 section 3.2): where meat enters the world, and where it leaves other than by a CORPSE_FOOD or CORPSE transfer.
MEAT_SOURCE_BODY_AT_DEATH = "BODY_AT_DEATH"
MEAT_SINK_CORPSE_DECAY = "CORPSE_DECAY"


def body_meat(entity: "EntityState") -> List[ItemStack]:
    """The raw meat stack a dead ``entity`` leaves, or none when its body feeds no meat (read once per death, from content)."""
    _, body = get_kind_properties(get_species_id_str(entity))
    if body is None or body.meat_yield <= 0 or "meat" not in (body.edible_as or ()):
        return []
    return [ItemStack(item_id=RAW_MEAT_ITEM, quantity=int(body.meat_yield))]
