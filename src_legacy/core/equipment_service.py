from __future__ import annotations
from typing import Dict, Any, Optional, List
from src_legacy.core.state import EntityState, EquipSlot, ItemKind
from src_legacy.core.items import ItemRegistry, ItemDefinition

class EquipmentService:
    """Service for ranking gear and making equipment decisions."""

    @staticmethod
    def get_gear_score(entity: EntityState, item_defn: ItemDefinition) -> float:
        """Calculate a score for an item based on entity role and class."""
        if item_defn.kind not in [ItemKind.WEAPON, ItemKind.ARMOR]:
            return 0.0

        score = 0.0
        role = entity.identity.role
        class_id = entity.identity.class_id

        # Weights based on class
        # In a full M8 implementation, these would come from a class registry
        weights = {
            "WARRIOR": {"atk_bonus": 1.0, "def_bonus": 1.5, "hp_bonus": 1.2},
            "MAGE": {"atk_bonus": 1.5, "def_bonus": 0.5, "int_bonus": 2.0},
            "ROGUE": {"atk_bonus": 1.2, "def_bonus": 0.8, "speed_bonus": 1.5},
            "NOVICE": {"atk_bonus": 1.0, "def_bonus": 1.0}
        }

        class_weights = weights.get(class_id, weights["NOVICE"])

        for prop, value in item_defn.properties.items():
            weight = class_weights.get(prop, 1.0)
            if isinstance(value, (int, float)):
                score += value * weight

        return score

    @staticmethod
    def should_replace(entity: EntityState, new_item_id: str, slot: EquipSlot) -> bool:
        """Determine if a new item is better than what's currently equipped."""
        new_defn = ItemRegistry.get(new_item_id)
        if not new_defn:
            return False

        current_item_id = entity.equipment.slots.get(slot)
        if not current_item_id:
            return True # Anything is better than nothing

        current_defn = ItemRegistry.get(current_item_id)
        if not current_defn:
            return True

        current_score = EquipmentService.get_gear_score(entity, current_defn)
        new_score = EquipmentService.get_gear_score(entity, new_defn)

        return new_score > current_score
