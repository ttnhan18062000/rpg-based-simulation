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
