from __future__ import annotations

from typing import Optional

from src.core.items import ItemDefinition, ItemRegistry
from src.core.state import EntityState, EquipSlot, ItemKind
from src.core.updates import EntityUpdate, EquipmentUpdate


class EquipmentService:
    """
    Service for equipment scoring, replacement decisions, auto-equip, and repair.

    This is the canonical implementation.

    Compatibility:
        - get_gear_score(...) is the newer, entity-aware scoring API.
        - rank_item(...) is preserved for older tests/imports.
        - should_replace(...) is used when evaluating one candidate item.
        - auto_equip(...) scans inventory and proposes EquipmentUpdate.
        - repair_equipment(...) restores durability for one equipped slot.
    """
    
    _SCORABLE_GEAR_PROPERTIES = {
        "atk_bonus",
        "def_bonus",
        "hp_bonus",
        "speed_bonus",
        "int_bonus",
        "range_bonus",
        "crit_bonus",
        "evasion_bonus",
    }

    @staticmethod
    def get_gear_score(entity: EntityState, item_defn: ItemDefinition) -> float:
        """
        Calculate a gear score for an item based on entity class.

        Only weapons and armor are considered equipment for scoring.
        Non-equipment items return 0.0.
        """
        if item_defn.kind not in (ItemKind.WEAPON, ItemKind.ARMOR):
            return 0.0

        class_id = entity.identity.class_id or "NOVICE"

        weights = {
            "WARRIOR": {
                "atk_bonus": 1.0,
                "def_bonus": 1.5,
                "hp_bonus": 1.2,
                "int_bonus": 0.5,
                "speed_bonus": 1.0,
            },
            "MAGE": {
                "atk_bonus": 1.5,
                "def_bonus": 0.5,
                "hp_bonus": 0.8,
                "int_bonus": 2.0,
                "speed_bonus": 1.0,
            },
            "ROGUE": {
                "atk_bonus": 1.2,
                "def_bonus": 0.8,
                "hp_bonus": 0.8,
                "int_bonus": 0.7,
                "speed_bonus": 1.5,
            },
            "NOVICE": {
                "atk_bonus": 1.0,
                "def_bonus": 1.0,
                "hp_bonus": 1.0,
                "int_bonus": 1.0,
                "speed_bonus": 1.0,
            },
        }

        class_weights = weights.get(class_id, weights["NOVICE"])

        score = 0.0

        for prop, value in item_defn.properties.items():
            if prop not in EquipmentService._SCORABLE_GEAR_PROPERTIES:
                continue

            if isinstance(value, (int, float)):
                score += value * class_weights.get(prop, 1.0)

        return score

    @staticmethod
    def rank_item(
        item_id: str,
        class_context: str = "NOVICE",
        entity: Optional[EntityState] = None,
    ) -> float:
        """
        Compatibility scoring API.

        Older code/tests may call:

            EquipmentService.rank_item("iron_sword")

        Newer code should prefer:

            EquipmentService.get_gear_score(entity, item_defn)

        If entity is provided, use full entity-aware scoring.
        Otherwise, use class_context-based scoring.
        """
        item_defn = ItemRegistry.get(item_id)

        if not item_defn:
            return 0.0

        if entity is not None:
            return EquipmentService.get_gear_score(entity, item_defn)

        if item_defn.kind not in (ItemKind.WEAPON, ItemKind.ARMOR):
            return 0.0

        class_id = class_context or "NOVICE"

        weights = {
            "WARRIOR": {
                "atk_bonus": 1.0,
                "def_bonus": 1.5,
                "hp_bonus": 1.2,
            },
            "MAGE": {
                "atk_bonus": 1.5,
                "def_bonus": 0.5,
                "int_bonus": 2.0,
            },
            "ROGUE": {
                "atk_bonus": 1.2,
                "def_bonus": 0.8,
                "speed_bonus": 1.5,
            },
            "NOVICE": {
                "atk_bonus": 1.0,
                "def_bonus": 1.0,
                "hp_bonus": 1.0,
                "speed_bonus": 1.0,
                "int_bonus": 1.0,
            },
            "hero": {
                "atk_bonus": 1.0,
                "def_bonus": 1.0,
                "hp_bonus": 1.0,
                "speed_bonus": 1.0,
                "int_bonus": 1.0,
            },
        }

        class_weights = weights.get(class_id, weights["NOVICE"])

        score = 0.0

        for prop, value in item_defn.properties.items():
            if prop not in EquipmentService._SCORABLE_GEAR_PROPERTIES:
                continue

            if isinstance(value, (int, float)):
                score += value * class_weights.get(prop, 1.0)

        return score

    @staticmethod
    def should_replace(
        entity: EntityState,
        new_item_id: str,
        slot: EquipSlot,
    ) -> bool:
        """
        Determine whether a candidate item should replace the currently equipped
        item in the given slot.
        """
        new_defn = ItemRegistry.get(new_item_id)

        if not new_defn:
            return False

        current_item_id = entity.equipment.slots.get(slot)

        if not current_item_id:
            return True

        current_defn = ItemRegistry.get(current_item_id)

        if not current_defn:
            return True

        current_score = EquipmentService.get_gear_score(entity, current_defn)
        new_score = EquipmentService.get_gear_score(entity, new_defn)

        return new_score > current_score

    @staticmethod
    def auto_equip(entity: EntityState) -> Optional[EntityUpdate]:
        """
        Scan inventory for better equipment and return an EntityUpdate if any
        slot should be changed.

        Important:
            This only proposes equipment slot changes.
            It does not directly mutate the entity.
        """
        equipment_changes: dict[EquipSlot, str] = {}

        for stack in entity.inventory.items:
            item_defn = ItemRegistry.get(stack.item_id)

            if not item_defn:
                continue

            if item_defn.kind not in (ItemKind.WEAPON, ItemKind.ARMOR):
                continue

            raw_slot = item_defn.properties.get("slot")

            if raw_slot is None:
                continue

            slot = EquipmentService._normalize_slot(raw_slot)

            if slot is None:
                continue

            if EquipmentService.should_replace(entity, stack.item_id, slot):
                equipment_changes[slot] = stack.item_id

        if not equipment_changes:
            return None

        return EntityUpdate(
            entity_id=entity.id,
            equipment=EquipmentUpdate(
                slot_updates=equipment_changes,
            ),
        )

    @staticmethod
    def repair_equipment(
        entity: EntityState,
        slot: EquipSlot,
        current_tick: int,
    ) -> Optional[EquipmentUpdate]:
        """
        Return an EquipmentUpdate that restores durability for one equipped slot.

        current_tick is accepted for future repair rules and compatibility.
        """
        item_id = entity.equipment.slots.get(slot)

        if not item_id:
            return None

        current_durability = entity.equipment.durability.get(slot, 100.0)

        if current_durability >= 100.0:
            return None

        return EquipmentUpdate(
            durability_delta={
                slot: 100.0 - current_durability,
            },
        )

    @staticmethod
    def _normalize_slot(raw_slot) -> Optional[EquipSlot]:
        """
        Normalize registry slot metadata into EquipSlot.

        Supports:
            - EquipSlot enum value
            - enum name string, e.g. "WEAPON"
            - enum value string, e.g. "weapon"
        """
        if isinstance(raw_slot, EquipSlot):
            return raw_slot

        if isinstance(raw_slot, str):
            if raw_slot in EquipSlot.__members__:
                return EquipSlot[raw_slot]

            for slot in EquipSlot:
                if raw_slot == slot.value:
                    return slot

        return None