"""A staged change to a building: its health, whether it works, its purse, its price modifiers and its maintenance-shift count.
`src/core/updates.py` re-exports it."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Optional

from src.core.update_models.inventory import InventoryUpdate


@dataclass(frozen=True, slots=True)
class BuildingUpdate:
    """Updates to building health/status."""
    building_id: int
    hp_delta: int = 0
    functional_set: Optional[bool] = None
    inventory: Optional[InventoryUpdate] = None
    price_modifiers_set: Optional[Dict[str, float]] = None
    # Maintenance shifts done this upkeep period (EXCH-02, ruling 61): a paid shift adds to the counter (``delta``) and the period reset sets it
    # to 0 (``set``). The apply path applies the set first, then the delta, so a reset on the tick a shift is paid cannot lose that shift.
    maintenance_shifts_done_delta: int = 0
    maintenance_shifts_done_set: Optional[int] = None

    def merge(self, other: BuildingUpdate) -> BuildingUpdate:
        """Fold a later update of the same building into this one: deltas add, a later set wins."""
        if self.building_id != other.building_id:
            raise ValueError("Cannot merge BuildingUpdates for different buildings")
        
        merged_inventory = self.inventory
        if self.inventory and other.inventory:
            merged_inventory = self.inventory.merge(other.inventory)
        elif other.inventory:
            merged_inventory = other.inventory

        return replace(self,
            hp_delta=self.hp_delta + other.hp_delta,
            functional_set=other.functional_set if other.functional_set is not None else self.functional_set,
            inventory=merged_inventory,
            price_modifiers_set=other.price_modifiers_set if other.price_modifiers_set is not None else self.price_modifiers_set,
            maintenance_shifts_done_delta=self.maintenance_shifts_done_delta + other.maintenance_shifts_done_delta,
            maintenance_shifts_done_set=other.maintenance_shifts_done_set if other.maintenance_shifts_done_set is not None else self.maintenance_shifts_done_set,
        )
