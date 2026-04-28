from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Set
from dataclasses import replace, dataclass

from src.core.updates import EntityUpdate, IdentityUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate

@dataclass(frozen=True, slots=True)
class V2Recipe:
    recipe_id: str
    output_item: str
    gold_cost: int
    materials: Dict[str, int]

class BlacksmithSystem:
    """
    Authoritative handler for crafting and recipe management.
    Law of Materials: Crafting must consume exact materials and gold.
    """

    # Parity with V1 RECIPES
    RECIPES: Dict[str, V2Recipe] = {
        "craft_steel_sword": V2Recipe(
            recipe_id="craft_steel_sword",
            output_item="steel_sword",
            gold_cost=60,
            materials={"iron_ore": 2, "wood": 1}
        ),
        "craft_battle_axe": V2Recipe(
            recipe_id="craft_battle_axe",
            output_item="battle_axe",
            gold_cost=90,
            materials={"iron_ore": 3, "steel_bar": 1}
        ),
        "craft_enchanted_blade": V2Recipe(
            recipe_id="craft_enchanted_blade",
            output_item="enchanted_blade",
            gold_cost=200,
            materials={"steel_bar": 2, "enchanted_dust": 2}
        ),
        "craft_iron_plate": V2Recipe(
            recipe_id="craft_iron_plate",
            output_item="iron_plate",
            gold_cost=70,
            materials={"iron_ore": 3, "leather": 1}
        ),
        "craft_enchanted_robe": V2Recipe(
            recipe_id="craft_enchanted_robe",
            output_item="enchanted_robe",
            gold_cost=150,
            materials={"leather": 2, "enchanted_dust": 1}
        ),
        "craft_ring_of_power": V2Recipe(
            recipe_id="craft_ring_of_power",
            output_item="ring_of_power",
            gold_cost=120,
            materials={"iron_ore": 1, "enchanted_dust": 1}
        ),
        "craft_evasion_amulet": V2Recipe(
            recipe_id="craft_evasion_amulet",
            output_item="evasion_amulet",
            gold_cost=80,
            materials={"leather": 2, "wood": 1}
        ),
        "craft_wolf_cloak": V2Recipe(
            recipe_id="craft_wolf_cloak",
            output_item="wolf_cloak",
            gold_cost=50,
            materials={"wolf_pelt": 2, "leather": 1}
        ),
        "craft_fang_necklace": V2Recipe(
            recipe_id="craft_fang_necklace",
            output_item="fang_necklace",
            gold_cost=45,
            materials={"wolf_fang": 2, "fiber": 1}
        ),
        "craft_desert_bow": V2Recipe(
            recipe_id="craft_desert_bow",
            output_item="desert_bow",
            gold_cost=75,
            materials={"raw_gem": 1, "fiber": 2}
        ),
        "craft_bone_shield": V2Recipe(
            recipe_id="craft_bone_shield",
            output_item="bone_shield",
            gold_cost=65,
            materials={"bone_shard": 3, "dark_moss": 1}
        ),
        "craft_spectral_blade": V2Recipe(
            recipe_id="craft_spectral_blade",
            output_item="spectral_blade",
            gold_cost=180,
            materials={"ectoplasm": 2, "enchanted_dust": 1}
        ),
        "craft_mountain_plate": V2Recipe(
            recipe_id="craft_mountain_plate",
            output_item="mountain_plate",
            gold_cost=160,
            materials={"stone_block": 3, "iron_ore": 2}
        ),
        "craft_herbal_remedy": V2Recipe(
            recipe_id="craft_herbal_remedy",
            output_item="herbal_remedy",
            gold_cost=15,
            materials={"herb": 3, "glowing_mushroom": 1}
        ),
    }

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
                    all_recipes = list(BlacksmithSystem.RECIPES.keys())
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
            
            recipe = BlacksmithSystem.RECIPES.get(craft_target)
            if not recipe:
                continue
            
            # Law of Knowledge: Must know the recipe
            if craft_target not in entity.identity.known_recipes:
                # (Optional: In M2 we might allow "auto-learn" at blacksmith if parity requires it)
                continue
            
            # Law of Resources: Check gold and materials
            if entity.inventory.gold < recipe.gold_cost:
                # Emit blockers on failure [Milestone 3]
                from src.systems.strategic import StrategicIntelligenceSystem
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
                from src.systems.strategic import StrategicIntelligenceSystem
                existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                strat_up = StrategicIntelligenceSystem.generate_crafting_blockers(
                    entity, recipe.materials, recipe.gold_cost
                )
                refined_entity_updates[e_id] = replace(existing_upd, strategic=strat_up)
                continue

            # Phase 3 Law: Resource Conservation (Atomic Crafting)
            from src.core.updates import ResourceTransferIntent
            from src.core.state import ItemStack
            
            materials = [ItemStack(mat, count) for mat, count in recipe.materials.items()]
            intent = ResourceTransferIntent(
                source_id=craft_target,
                source_kind="CRAFTING",
                items_add=[ItemStack(recipe.output_item, 1)],
                items_remove=materials,
                gold_delta=-recipe.gold_cost, # Note: intent uses gold_cost as positive for deduction in resolve
                gold_cost=recipe.gold_cost,
                transfer_kind="CRAFT"
            )
            
            # SUCCESS: Queue crafting transformation
            existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            refined_entity_updates[e_id] = replace(
                existing_upd,
                resource_transfers=list(existing_upd.resource_transfers) + [intent]
            )

        return replace(update, entity_updates=refined_entity_updates)
