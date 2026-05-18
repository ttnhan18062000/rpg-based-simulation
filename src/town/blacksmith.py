from __future__ import annotations
from typing import Optional, List, Dict
from src.core.state import AuthoritativeState, EntityState, BuildingState, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, InventoryUpdate
from src.core.recipes import RecipeRegistry, Recipe
from src.core.inventory import InventoryService

class BlacksmithService:
    """Manages crafting and repairs at the blacksmith."""

    @staticmethod
    def craft_item(
        entity: EntityState, 
        recipe_id: str, 
        state: AuthoritativeState
    ) -> Optional[StateUpdate]:
        """Entity crafts an item using materials."""
        # 1. Proximity to Blacksmith
        blacksmith = next((b for b in state.buildings.values() if b.kind == "blacksmith" and b.functional), None)
        if not blacksmith:
            return None
            
        dist = abs(entity.position[0] - blacksmith.position[0]) + abs(entity.position[1] - blacksmith.position[1])
        if dist > 2.0:
            return None
            
        # 2. Check Recipe
        recipe = RecipeRegistry.get_recipe(recipe_id)
        if not recipe:
            return None
            
        # 3. Check Materials
        mats_to_remove = []
        for mat_id, qty in recipe.materials.items():
            existing = next((s for s in entity.inventory.items if s.item_id == mat_id), None)
            if not existing or existing.quantity < qty:
                return None
            mats_to_remove.append(ItemStack(mat_id, qty))
            
        # 4. Check Gold
        if entity.inventory.gold < recipe.gold_cost:
            return None
            
        # 5. Check Capacity for result
        # We assume space will be freed by removing materials, but let's be safe
        # (InventoryService.can_add_item doesn't know about the removal yet)
        
        # 6. Generate Transaction Intent
        from src.core.updates import ResourceTransferIntent
        intent = ResourceTransferIntent(
            source_id=blacksmith.id,
            source_kind="CRAFTING",
            items_remove=mats_to_remove,
            items_add=[ItemStack(recipe.result_item_id, recipe.result_quantity)],
            gold_cost=recipe.gold_cost,
            transfer_kind="CRAFT"
        )
        
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    resource_transfers=[intent]
                )
            }
        )

class BlacksmithAction:
    """Action wrapper for economy tests."""
    @staticmethod
    def craft(entity: EntityState, recipe_id: str, state: AuthoritativeState) -> Optional[EntityUpdate]:
        res = BlacksmithService.craft_item(entity, recipe_id, state)
        if res and entity.id in res.entity_updates:
            return res.entity_updates[entity.id]
        return None
