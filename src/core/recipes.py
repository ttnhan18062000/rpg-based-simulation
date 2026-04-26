from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass(frozen=True, slots=True)
class Recipe:
    id: str
    name: str
    materials: Dict[str, int] # ItemID -> Quantity
    result_item_id: str
    result_quantity: int = 1
    gold_cost: int = 0
    required_role: Optional[int] = None # Optional role requirement

class RecipeRegistry:
    """Central registry for all craftable items."""
    
    _recipes: Dict[str, Recipe] = {
        "iron_sword": Recipe(
            id="iron_sword",
            name="Iron Sword",
            materials={"iron_ore": 5, "wood": 2},
            result_item_id="iron_sword",
            gold_cost=50
        ),
        "iron_shield": Recipe(
            id="iron_shield",
            name="Iron Shield",
            materials={"iron_ore": 8},
            result_item_id="iron_shield",
            gold_cost=80
        ),
        "health_potion": Recipe(
            id="health_potion",
            name="Health Potion",
            materials={"herb": 3},
            result_item_id="health_potion",
            gold_cost=20
        )
    }

    @classmethod
    def get_recipe(cls, recipe_id: str) -> Optional[Recipe]:
        return cls._recipes.get(recipe_id)

    @classmethod
    def get_all(cls) -> List[Recipe]:
        return list(cls._recipes.values())
