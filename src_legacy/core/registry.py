from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class ItemData:
    id: str
    name: str
    value: int
    rarity: str = "COMMON"
    weight: float = 1.0
    equip_slot: Optional[str] = None # e.g., "MAIN_HAND", "TORSO"
    atk_bonus: int = 0
    def_bonus: int = 0
    hp_bonus: int = 0
    spd_bonus: int = 0

@dataclass(frozen=True)
class CraftingRecipe:
    id: str
    output_item: str
    materials: Dict[str, int]
    gold_cost: int = 0
    duration: int = 1

@dataclass(frozen=True)
class SkillData:
    id: str
    name: str
    base_damage: int
    ap_cost: int
    cooldown: int = 0
    required_level: int = 1
    required_class: Optional[str] = None

class Registry:
    """Authoritative truth for world constants and data."""
    
    SKILLS: Dict[str, SkillData] = {
        "basic_attack": SkillData("basic_attack", "Basic Attack", base_damage=0, ap_cost=2, cooldown=0),
        "heavy_strike": SkillData("heavy_strike", "Heavy Strike", base_damage=15, ap_cost=4, cooldown=3, required_level=5, required_class="WARRIOR"),
        "fireball": SkillData("fireball", "Fireball", base_damage=25, ap_cost=5, cooldown=4, required_level=5, required_class="MAGE"),
        "heal": SkillData("heal", "Heal", base_damage=-20, ap_cost=4, cooldown=4, required_level=3, required_class="CLERIC")
    }
    
    ITEMS: Dict[str, ItemData] = {
        "wood": ItemData("wood", "Wood", 5),
        "iron_ore": ItemData("iron_ore", "Iron Ore", 10),
        "iron_sword": ItemData("iron_sword", "Iron Sword", 50, equip_slot="MAIN_HAND", atk_bonus=5),
        "steel_sword": ItemData("steel_sword", "Steel Sword", 150, equip_slot="MAIN_HAND", atk_bonus=12),
        "iron_plate": ItemData("iron_plate", "Iron Plate", 70, equip_slot="TORSO", def_bonus=8, hp_bonus=20),
        "herbal_remedy": ItemData("herbal_remedy", "Herbal Remedy", 25),
        "fish": ItemData("fish", "Fish", 5),
        "leather": ItemData("leather", "Leather", 8),
        "fiber": ItemData("fiber", "Fiber", 3),
        "herb": ItemData("herb", "Herb", 4),
    }
    
    RECIPES: Dict[str, CraftingRecipe] = {
        "craft_steel_sword": CraftingRecipe("craft_steel_sword", "steel_sword", {"iron_ore": 2, "wood": 1}, gold_cost=60),
        "craft_battle_axe": CraftingRecipe("craft_battle_axe", "battle_axe", {"iron_ore": 3, "steel_bar": 1}, gold_cost=90),
        "craft_enchanted_blade": CraftingRecipe("craft_enchanted_blade", "enchanted_blade", {"steel_bar": 2, "enchanted_dust": 2}, gold_cost=200),
        "craft_iron_plate": CraftingRecipe("craft_iron_plate", "iron_plate", {"iron_ore": 3, "leather": 1}, gold_cost=70),
        "craft_enchanted_robe": CraftingRecipe("craft_enchanted_robe", "enchanted_robe", {"leather": 2, "enchanted_dust": 1}, gold_cost=150),
        "craft_ring_of_power": CraftingRecipe("craft_ring_of_power", "ring_of_power", {"iron_ore": 1, "enchanted_dust": 1}, gold_cost=120),
        "craft_evasion_amulet": CraftingRecipe("craft_evasion_amulet", "evasion_amulet", {"leather": 2, "wood": 1}, gold_cost=80),
        "craft_wolf_cloak": CraftingRecipe("craft_wolf_cloak", "wolf_cloak", {"wolf_pelt": 2, "leather": 1}, gold_cost=50),
        "craft_fang_necklace": CraftingRecipe("craft_fang_necklace", "fang_necklace", {"wolf_fang": 2, "fiber": 1}, gold_cost=45),
        "craft_desert_bow": CraftingRecipe("craft_desert_bow", "desert_bow", {"raw_gem": 1, "fiber": 2}, gold_cost=75),
        "craft_bone_shield": CraftingRecipe("craft_bone_shield", "bone_shield", {"bone_shard": 3, "dark_moss": 1}, gold_cost=65),
        "craft_spectral_blade": CraftingRecipe("craft_spectral_blade", "spectral_blade", {"ectoplasm": 2, "enchanted_dust": 1}, gold_cost=180),
        "craft_mountain_plate": CraftingRecipe("craft_mountain_plate", "mountain_plate", {"iron_ore": 5, "stone": 3}, gold_cost=130),
    }

    @staticmethod
    def get_item(item_id: str) -> Optional[ItemData]:
        return Registry.ITEMS.get(item_id.lower())

    @staticmethod
    def get_recipe(recipe_id: str) -> Optional[CraftingRecipe]:
        return Registry.RECIPES.get(recipe_id.lower())
