from __future__ import annotations
from typing import Optional
from src.core.state import EntityState, AuthoritativeState, ItemKind
from src.core.updates import EntityUpdate, EquipmentUpdate
from src.core.items import ItemRegistry

class EquipmentService:
    """Logic for gear ranking and automated equipment selection."""

    @staticmethod
    def rank_item(item_id: str, class_context: str = "hero") -> float:
        """
        Calculate a power score for an item based on its properties.
        Simplified for M5: weighted sum of atk_bonus and def_bonus.
        """
        defn = ItemRegistry.get(item_id)
        if not defn:
            return 0.0
            
        score = 0.0
        props = defn.properties
        
        # Power weights by class (placeholder logic)
        atk_weight = 1.0
        def_weight = 1.0
        
        score += props.get("atk_bonus", 0) * atk_weight
        score += props.get("def_bonus", 0) * def_weight
        
        return score

    @staticmethod
    def auto_equip(entity: EntityState) -> Optional[EntityUpdate]:
        """
        Scan inventory for better gear in each slot and return an update if changes needed.
        """
        current_eq = entity.equipment.slots
        inventory_items = entity.inventory.items
        
        equipment_changes = {}
        
        # Check for better gear in inventory
        for stack in inventory_items:
            defn = ItemRegistry.get(stack.item_id)
            if not defn:
                continue
                
            slot = defn.properties.get("slot")
            if not slot:
                continue
                
            # Compare with current
            current_item_id = current_eq.get(slot)
            current_power = 0.0
            if current_item_id:
                current_power = EquipmentService.rank_item(current_item_id)
                
            new_power = EquipmentService.rank_item(stack.item_id)
            
            if new_power > current_power:
                equipment_changes[slot] = stack.item_id
                
        if not equipment_changes:
            return None
            
        return EntityUpdate(
            entity_id=entity.id,
            equipment=EquipmentUpdate(slot_updates=equipment_changes)
        )
