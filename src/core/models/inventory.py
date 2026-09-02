# Compliance IDs: TOWN-013
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any
from enum import Enum

class ItemKind(str, Enum):
    """Broad categories of items."""
    MATERIAL = "MATERIAL"
    CONSUMABLE = "CONSUMABLE"
    WEAPON = "WEAPON"
    ARMOR = "ARMOR"
    CURRENCY = "CURRENCY"

class EquipSlot(str, Enum):
    """Valid equipment locations on an entity."""
    HEAD = "HEAD"
    TORSO = "TORSO"
    LEGS = "LEGS"
    MAIN_HAND = "MAIN_HAND"
    OFF_HAND = "OFF_HAND"

@dataclass(frozen=True, slots=True)
class ItemStack:
    """A quantity of a specific item template."""
    item_id: str
    quantity: int = 1
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "id": self.item_id,
            "q": self.quantity
        }

@dataclass(frozen=True, slots=True)
class InventoryComponent:
    """
    Bounded container for items and gold.
    Logic ID: TOWN-013 (Inventory is bounded by slots and weight)
    """
    items: List[ItemStack] = field(default_factory=list)
    gold: int = 0
    max_slots: int = 16
    max_weight: float = 50.0
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "gold": self.gold,
            "items": [i.to_canonical_dict() for i in sorted(self.items, key=lambda x: x.item_id)],
            "max_slots": self.max_slots
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res

class AcquiredMethod(str, Enum):
    LOOT = "LOOT"
    CRAFTED = "CRAFTED"
    GIFT = "GIFT"
    INHERITED = "INHERITED"

@dataclass(frozen=True, slots=True)
class ItemInstance:
    """A durable per-physical-item ownership record. Additive sidecar to ItemStack — never
    replaces the ItemStack entry in InventoryComponent.items. See docs/mechanics/03_economic_laws.md
    (once updated) for the governing law."""
    instance_id: int
    item_id: str
    owner_history: List[str]
    acquired_tick: int
    acquired_method: AcquiredMethod
