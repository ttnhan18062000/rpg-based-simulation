from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from src.core.state import ItemKind, EquipSlot

@dataclass(frozen=True, slots=True)
class ItemDefinition:
    """Static template for an item."""
    id: str
    name: str
    kind: ItemKind
    weight: float = 0.1
    stack_size: int = 20
    value: int = 1
    properties: Dict[str, Any] = field(default_factory=dict)

class ItemRegistry:
    """Central database of item templates."""
    _items: Dict[str, ItemDefinition] = {
        "iron_ore": ItemDefinition(
            id="iron_ore", name="Iron Ore", kind=ItemKind.MATERIAL, weight=2.0
        ),
        "wood": ItemDefinition(
            id="wood", name="Wood", kind=ItemKind.MATERIAL, weight=1.0
        ),
        "WOOD": ItemDefinition(
            id="WOOD", name="Wood", kind=ItemKind.MATERIAL, weight=1.0
        ),
        "herb": ItemDefinition(
            id="herb", name="Herb", kind=ItemKind.MATERIAL, weight=0.1
        ),
        "bread": ItemDefinition(
            id="bread", name="Bread", kind=ItemKind.CONSUMABLE, weight=0.2, 
            properties={"heal_amount": 20, "hunger_recovery": 30.0}
        ),
        "healing_potion": ItemDefinition(
            id="healing_potion", name="Healing Potion", kind=ItemKind.CONSUMABLE, weight=0.5,
            value=100,
            properties={"heal_amount": 50}
        ),
        "iron_sword": ItemDefinition(
            id="iron_sword", name="Iron Sword", kind=ItemKind.WEAPON, weight=5.0, stack_size=1,
            properties={"atk_bonus": 10, "range": 1, "slot": EquipSlot.MAIN_HAND}
        ),
        "steel_sword": ItemDefinition(
            id="steel_sword", name="Steel Sword", kind=ItemKind.WEAPON, weight=6.0, stack_size=1,
            properties={"atk_bonus": 18, "range": 1, "slot": EquipSlot.MAIN_HAND}
        ),
        "iron_plate": ItemDefinition(
            id="iron_plate", name="Iron Plate", kind=ItemKind.ARMOR, weight=12.0, stack_size=1,
            properties={"def_bonus": 15, "slot": EquipSlot.TORSO}
        ),
        "leather_armor": ItemDefinition(
            id="leather_armor", name="Leather Armor", kind=ItemKind.ARMOR, weight=8.0, stack_size=1,
            properties={"def_bonus": 5, "slot": EquipSlot.TORSO}
        ),
        "wooden_staff": ItemDefinition(
            id="wooden_staff", name="Wooden Staff", kind=ItemKind.WEAPON, weight=3.0, stack_size=1,
            properties={"atk_bonus": 5, "range": 2, "slot": EquipSlot.MAIN_HAND}
        ),
        "iron_dagger": ItemDefinition(
            id="iron_dagger", name="Iron Dagger", kind=ItemKind.WEAPON, weight=1.0, stack_size=1,
            properties={"atk_bonus": 4, "range": 1, "slot": EquipSlot.MAIN_HAND}
        ),
        "wooden_club": ItemDefinition(
            id="wooden_club", name="Wooden Club", kind=ItemKind.WEAPON, weight=4.0, stack_size=1,
            properties={"atk_bonus": 3, "range": 1, "slot": EquipSlot.MAIN_HAND}
        ),
        "gold_coin": ItemDefinition(
            id="gold_coin", name="Gold Coin", kind=ItemKind.CURRENCY, weight=0.001, stack_size=999
        ),
        "gold": ItemDefinition(
            id="gold", name="Gold", kind=ItemKind.CURRENCY, weight=0.001, stack_size=999999
        ),
        "ore": ItemDefinition(
            id="ore", name="Ore", kind=ItemKind.MATERIAL, weight=5.0
        ),
        "ORE": ItemDefinition(
            id="ORE", name="Ore", kind=ItemKind.MATERIAL, weight=5.0
        ),
        "stone": ItemDefinition(
            id="stone", name="Stone", kind=ItemKind.MATERIAL, weight=1.0
        )
    }

    @classmethod
    def get(cls, item_id: str) -> Optional[ItemDefinition]:
        return cls._items.get(item_id)
