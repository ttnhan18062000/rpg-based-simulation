from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Set
from dataclasses import replace, dataclass

from src_legacy.core.updates import EntityUpdate, InventoryUpdate, IdentityUpdate

if TYPE_CHECKING:
    from src_legacy.core.state import AuthoritativeState, EntityState
    from src_legacy.core.updates import StateUpdate

from src_legacy.core.registry import Registry

class BlacksmithSystem:
    """
    Authoritative handler for crafting and recipe management.
    Law of Materials: Crafting must consume exact materials and gold.
    """

    @staticmethod
    def enforce(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Refine the proposed update according to crafting and knowledge laws.
        """
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, entity in state.entities.items():
            pos = entity.position
            ent_upd = refined_entity_updates.get(e_id)
            if ent_upd and ent_upd.new_position:
                pos = ent_upd.new_position
                
            tile_pos = (int(pos[0]), int(pos[1]))
            building_type = state.building_tiles.get(tile_pos)
            
            # --- Law of Knowledge (Wholesale Learning) ---
            if building_type == "blacksmith":
                # Check functionality (LEG-RPG-001/006)
                building = next((b for b in state.buildings.values() if b.position == tile_pos and b.kind == "blacksmith"), None)
                if building and not building.functional:
                    continue # Blacksmith is sabotaged and non-functional
                
                if not entity.identity.known_recipes:
                    existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                    existing_id = existing_upd.identity if existing_upd.identity else IdentityUpdate()
                    
                    # Wholesale learning (Parity with V1)
                    all_recipes = list(Registry.RECIPES.keys())
                    new_id = replace(existing_id, recipes_learned=all_recipes)
                    
                    refined_entity_updates[e_id] = replace(
                        existing_upd,
                        identity=new_id
                    )
                    continue # Skip crafting check if we just learned recipes this tick? 
                         # Actually V1 does both if possible.

            # --- Law of Materials (Crafting) ---
            # Check for explicit crafting intent
            craft_target = entity.identity.craft_target
            
            # Allow AI to propose a new craft_target via IdentityUpdate
            if ent_upd and ent_upd.identity and ent_upd.identity.craft_target:
                craft_target = ent_upd.identity.craft_target

            if not craft_target:
                continue

            if building_type != "blacksmith":
                continue
            
            recipe = Registry.get_recipe(craft_target)
            if not recipe:
                continue
            
            # Law of Knowledge: Must know the recipe
            if craft_target not in entity.identity.known_recipes:
                # (Optional: In M2 we might allow "auto-learn" at blacksmith if parity requires it)
                continue
            
            # Law of Resources: Check gold and materials
            if entity.inventory.gold < recipe.gold_cost:
                # Emit blockers on failure [Milestone 3]
                from src_legacy.systems.strategic import StrategicIntelligenceSystem
                existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                strat_up = StrategicIntelligenceSystem.generate_crafting_blockers(
                    entity, recipe.materials, recipe.gold_cost
                )
                refined_entity_updates[e_id] = replace(existing_upd, strategic=strat_up)
                continue
                
            can_craft = True
            for mat, count in recipe.materials.items():
                have = sum((s.quantity if hasattr(s, "quantity") else 1) for s in entity.inventory.items if (s.item_id if hasattr(s, "item_id") else s) == mat)
                if have < count:
                    can_craft = False
                    break
            
            if not can_craft:
                # Emit blockers on failure [Milestone 3]
                from src_legacy.systems.strategic import StrategicIntelligenceSystem
                existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                strat_up = StrategicIntelligenceSystem.generate_crafting_blockers(
                    entity, recipe.materials, recipe.gold_cost
                )
                refined_entity_updates[e_id] = replace(existing_upd, strategic=strat_up)
                continue
            
            # CAPACITY CHECK
            from src_legacy.core.inventory import InventoryService
            from src_legacy.core.state import ItemStack
            output_stack = ItemStack(recipe.output_item, 1)
            # Create a virtual inventory that doesn't have the materials we're about to remove
            # Actually, can_add_items already handles the net change if we are careful.
            # For simplicity: check if it can add the output item to current inventory.
            # (Strictly speaking, removing materials might free up space, but we want to be safe)
            if not InventoryService.can_add_item(entity.inventory, recipe.output_item, 1):
                # ABORT due to pressure
                # (Optional: emit a strategic blocker for INVENTORY_FULL)
                continue
                
            # SUCCESS: Apply crafting transformation
            existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            # 1. Deduct Materials & Gold, Add Output
            existing_inv = existing_upd.inventory if existing_upd.inventory else InventoryUpdate()
            new_removed = list(existing_inv.items_remove)
            from src_legacy.core.state import ItemStack
            for mat, count in recipe.materials.items():
                new_removed.append(ItemStack(mat, count))
            
            new_added = list(existing_inv.items_add)
            new_added.append(ItemStack(recipe.output_item, 1))
            
            new_inv = replace(
                existing_inv,
                items_add=new_added,
                items_remove=new_removed,
                gold_delta=existing_inv.gold_delta - recipe.gold_cost
            )
            
            # 2. Reset Craft Target (Consumed)
            existing_id = existing_upd.identity if existing_upd.identity else IdentityUpdate()
            new_id = replace(existing_id, craft_target="")
            
            refined_entity_updates[e_id] = replace(
                existing_upd,
                inventory=new_inv,
                identity=new_id
            )

        return replace(update, entity_updates=refined_entity_updates)
