from __future__ import annotations
from typing import Any
from pydantic import Field
from src.core.models.base import Aspect

class InventoryAspect(Aspect):
    """Aspect handling items, equipment, and weight management."""
    items: list[str] = Field(default_factory=list)
    max_slots: int = 8
    max_weight: float = 20.0
    weapon: str | None = None
    armor: str | None = None
    accessory: str | None = None
    
    # Home storage (heroes only)
    home_storage: Any = None

    def model_copy(self, **kwargs) -> InventoryAspect:
        """Deep copy items and home_storage even on shallow aspect copy."""
        copy_obj = super().model_copy(**kwargs)
        copy_obj.items = list(self.items) # Always ensure new list object
        if self.home_storage and hasattr(self.home_storage, "copy"):
            copy_obj.home_storage = self.home_storage.copy()
        return copy_obj

    def __eq__(self, other: Any) -> bool:
        if not hasattr(other, "items"): return False
        return (
            list(self.items) == list(other.items) and
            self.max_slots == getattr(other, "max_slots", -1) and
            abs(self.max_weight - getattr(other, "max_weight", 0.0)) < 0.001 and
            self.weapon == getattr(other, "weapon", None) and
            self.armor == getattr(other, "armor", None) and
            self.accessory == getattr(other, "accessory", None)
        )

    @property
    def used_slots(self) -> int:
        return len(self.items)

    @property
    def is_full(self) -> bool:
        return self.used_slots >= self.max_slots

    @property
    def current_weight(self) -> float:
        total = 0.0
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        for iid in self.items:
            t = ITEM_REGISTRY.get(iid)
            if t: total += t.weight
        for slot_id in (self.weapon, self.armor, self.accessory):
            if slot_id:
                t = ITEM_REGISTRY.get(slot_id)
                if t: total += t.weight
        return total

    @property
    def total_weight(self) -> float:
        return self.current_weight

    @property
    def is_effectively_full(self) -> bool:
        """True if inventory is full by slots or near weight limit."""
        return self.is_full or (self.current_weight >= self.max_weight * 0.9)

    @property
    def weight_ratio(self) -> float:
        """Ratio of current weight to max weight (0.0 to 1.0+)."""
        if self.max_weight <= 0:
            return 1.0
        return self.current_weight / self.max_weight

    def count_item(self, item_id: str) -> int:
        """Count how many copies of item_id are in the bag."""
        return self.items.count(item_id)

    def has_consumable(self, item_id: str) -> bool:
        """Check if item_id is in inventory Bag."""
        return item_id in self.items
    
    def can_add(self, item_id: str) -> bool:
        if self.used_slots >= self.max_slots: return False
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        t = ITEM_REGISTRY.get(item_id)
        if t is None: return False
        return self.current_weight + t.weight <= self.max_weight

    def add_item(self, item_id: str) -> bool:
        if not self.can_add(item_id): return False
        self.items.append(item_id)
        return True

    def remove_item(self, item_id: str) -> bool:
        if item_id in self.items:
            self.items.remove(item_id)
            return True
        return False

    def equip(self, item_id: str) -> bool:
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        from src.core.gameplay.items.items import ItemType
        t = ITEM_REGISTRY.get(item_id)
        if t is None or item_id not in self.items: return False
        if t.item_type == ItemType.WEAPON:
            if self.weapon: self.items.append(self.weapon)
            self.weapon = item_id
        elif t.item_type == ItemType.ARMOR:
            if self.armor: self.items.append(self.armor)
            self.armor = item_id
        elif t.item_type == ItemType.ACCESSORY:
            if self.accessory: self.items.append(self.accessory)
            self.accessory = item_id
        else: return False
        self.items.remove(item_id)
        return True

    def auto_equip_best(self, item_id: str, hero_class: Any = 0) -> bool:
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        from src.core.gameplay.items.items import ItemType, _item_power
        t = ITEM_REGISTRY.get(item_id)
        if t is None or item_id not in self.items: return False
        if t.item_type not in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY): return False
        if t.item_type == ItemType.WEAPON: current_id = self.weapon
        elif t.item_type == ItemType.ARMOR: current_id = self.armor
        else: current_id = self.accessory
        
        if current_id is None: return self.equip(item_id)
        current_t = ITEM_REGISTRY.get(current_id)
        if current_t is None or _item_power(t, hero_class) > _item_power(current_t, hero_class):
            return self.equip(item_id)
        return False

    def equipment_bonus(self, stat: str) -> int | float:
        total = 0
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        for slot_id in (self.weapon, self.armor, self.accessory):
            if slot_id:
                t = ITEM_REGISTRY.get(slot_id)
                if t: total += getattr(t, stat, 0)
        return total

    def get_all_item_ids(self) -> list[str]:
        result = list(self.items)
        if self.weapon: result.append(self.weapon)
        if self.armor: result.append(self.armor)
        if self.accessory: result.append(self.accessory)
        return result

    def copy_inventory(self) -> "InventoryAspect":
        """Compatibility for old inventory.copy() calls."""
        return InventoryAspect(**self.model_dump())


# Rebuild Model to finalize Pydantic setup
InventoryAspect.model_rebuild()
