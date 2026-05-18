from __future__ import annotations
from typing import Optional, List, Tuple
from src.core.state import EntityState, ItemStack
from src.core.recipes import RecipeRegistry, Recipe
from src.core.updates import InventoryUpdate, StrategicUpdate

class CraftingSystem:
    """
    Authoritative system for item creation and resource consumption.
    Enforces recipe knowledge, material availability, and capacity gates.
    """

    @staticmethod
    def craft(
        entity: EntityState,
        recipe_id: str,
        tick: int
    ) -> Tuple[Optional[InventoryUpdate], str]:
        """
        Processes a crafting attempt.
        Returns (InventoryUpdate, reason).
        """
        # 1. Recipe Check
        recipe = RecipeRegistry.get_recipe(recipe_id)
        if not recipe:
            return None, "UNKNOWN_RECIPE"
            
        # 2. Knowledge Gate
        if recipe_id not in entity.identity.known_recipes:
            return None, "RECIPE_NOT_LEARNED"
            
        # 3. Role/Skill Gate
        if recipe.required_role is not None and entity.identity.role != recipe.required_role:
            return None, "INSUFFICIENT_RANK"

        # 4. Material Check
        for material_id, quantity in recipe.materials.items():
            found_qty = sum(s.quantity for s in entity.inventory.items if s.item_id == material_id)
            if found_qty < quantity:
                return None, f"INSUFFICIENT_MATERIAL:{material_id}"

        # 5. Gold Check
        if entity.inventory.gold < recipe.gold_cost:
            return None, "INSUFFICIENT_GOLD"

        # 6. Capacity Check
        # Simplified: Check if there's at least one slot or if the item stacks
        if len(entity.inventory.items) >= entity.inventory.max_slots:
            # Check if result item can stack with existing
            can_stack = any(s.item_id == recipe.result_item_id for s in entity.inventory.items)
            if not can_stack:
                return None, "INVENTORY_FULL"

        # 7. Generate Update
        items_to_remove = []
        for mid, qty in recipe.materials.items():
            items_to_remove.append(ItemStack(item_id=mid, quantity=qty))
            
        result_item = ItemStack(item_id=recipe.result_item_id, quantity=recipe.result_quantity)
        
        return InventoryUpdate(
            items_remove=items_to_remove,
            items_add=[result_item],
            gold_delta=-recipe.gold_cost
        ), "SUCCESS"
