"""Town buildings — Shop, Blacksmith, Guild Hall, Class Hall, Inn.

Buildings are fixed locations in town that heroes can interact with.
Each building type provides different services:
  - Store: buy/sell items
  - Blacksmith: craft powerful items from materials + gold
  - Guild: get intel about enemy camps and material sources
  - Class Hall: learn new class skills, attempt breakthroughs
  - Inn: rest to recover HP and stamina quickly
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.core.enums import ItemType, Rarity
from src.core.items import ITEM_REGISTRY, ItemTemplate

if TYPE_CHECKING:
    from src.core.models import Vector2


# ---------------------------------------------------------------------------
# Building data model
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Building:
    """A fixed building in the town."""

    building_id: str          # "store", "blacksmith", "guild"
    name: str
    pos: Vector2
    building_type: str        # "store" | "blacksmith" | "guild"


# ---------------------------------------------------------------------------
# Shop economy — sell/buy prices
# ---------------------------------------------------------------------------

# Sell prices by rarity (gold received when hero sells to shop)
SELL_PRICES: dict[int, int] = {
    Rarity.COMMON: 5,
    Rarity.UNCOMMON: 15,
    Rarity.RARE: 40,
}


def item_sell_price(item_id: str) -> int:
    """Calculate how much gold a hero gets for selling an item."""
    t = ITEM_REGISTRY.get(item_id)
    if t is None:
        return 0
    if t.sell_value > 0:
        return t.sell_value
    if t.gold_value > 0:
        return t.gold_value
    return SELL_PRICES.get(t.rarity, 3)


# Items available for purchase at the store: (item_id, buy_price)
SHOP_INVENTORY: list[tuple[str, int]] = [
    # ---- Healing potions ----
    ("small_hp_potion", 15),
    ("medium_hp_potion", 40),
    ("large_hp_potion", 80),
    ("herbal_remedy", 20),
    # ---- Buff potions ----
    ("atk_potion", 25),
    ("def_potion", 25),
    ("spd_potion", 25),
    ("crit_potion", 45),
    ("antidote", 15),
    # ---- Weapons (tiered) ----
    ("wooden_club", 20),
    ("bandit_dagger", 35),
    ("iron_sword", 50),
    ("orc_axe", 65),
    ("steel_greatsword", 120),
    # ---- Magic weapons ----
    ("apprentice_staff", 30),
    ("fire_staff", 90),
    # ---- Armor (tiered) ----
    ("leather_vest", 25),
    ("chainmail", 60),
    ("orc_shield", 70),
    ("plate_armor", 150),
    # ---- Magic armor ----
    ("cloth_robe", 25),
    ("silk_robe", 60),
    # ---- Accessories ----
    ("lucky_charm", 30),
    ("speed_ring", 55),
    ("mana_crystal", 30),
    ("spirit_pendant", 55),
    # ---- Materials ----
    ("mana_shard", 30),
    ("silver_ingot", 35),
    ("phoenix_feather", 60),
]


def shop_buy_price(item_id: str) -> int | None:
    """Return the buy price for an item, or None if not sold at shop."""
    for iid, price in SHOP_INVENTORY:
        if iid == item_id:
            return price
    return None


# ---------------------------------------------------------------------------
# Blacksmith recipes
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Recipe:
    """A crafting recipe at the blacksmith."""

    recipe_id: str
    output_item: str          # item_id produced
    gold_cost: int
    materials: dict[str, int]  # {item_id: quantity}
    description: str = ""

    def to_dict(self) -> dict:
        t = ITEM_REGISTRY.get(self.output_item)
        return {
            "recipe_id": self.recipe_id,
            "output_item": self.output_item,
            "output_name": t.name if t else self.output_item,
            "gold_cost": self.gold_cost,
            "materials": dict(self.materials),
            "description": self.description,
        }


RECIPES: list[Recipe] = [
    # --- Goblin-material recipes ---
    Recipe(
        recipe_id="craft_steel_sword",
        output_item="steel_sword",
        gold_cost=60,
        materials={"iron_ore": 2, "wood": 1},
        description="A well-forged steel blade with improved balance.",
    ),
    Recipe(
        recipe_id="craft_battle_axe",
        output_item="battle_axe",
        gold_cost=90,
        materials={"iron_ore": 3, "steel_bar": 1},
        description="A heavy battle axe that hits hard but swings slow.",
    ),
    Recipe(
        recipe_id="craft_enchanted_blade",
        output_item="enchanted_blade",
        gold_cost=200,
        materials={"steel_bar": 2, "enchanted_dust": 2},
        description="A blade infused with magical energy. Requires rare dust.",
    ),
    Recipe(
        recipe_id="craft_iron_plate",
        output_item="iron_plate",
        gold_cost=70,
        materials={"iron_ore": 3, "leather": 1},
        description="Heavy iron plate armor. Strong defense at the cost of speed.",
    ),
    Recipe(
        recipe_id="craft_enchanted_robe",
        output_item="enchanted_robe",
        gold_cost=150,
        materials={"leather": 2, "enchanted_dust": 1},
        description="A light robe enchanted for agility and evasion.",
    ),
    Recipe(
        recipe_id="craft_ring_of_power",
        output_item="ring_of_power",
        gold_cost=120,
        materials={"iron_ore": 1, "enchanted_dust": 1},
        description="A ring that amplifies both attack and defense.",
    ),
    Recipe(
        recipe_id="craft_evasion_amulet",
        output_item="evasion_amulet",
        gold_cost=80,
        materials={"leather": 2, "wood": 1},
        description="An amulet carved from fine materials for enhanced agility.",
    ),
    # --- Wolf-material recipes (Forest) ---
    Recipe(
        recipe_id="craft_wolf_cloak",
        output_item="wolf_cloak",
        gold_cost=50,
        materials={"wolf_pelt": 2, "leather": 1},
        description="A light cloak sewn from wolf pelts. Fast and evasive.",
    ),
    Recipe(
        recipe_id="craft_fang_necklace",
        output_item="fang_necklace",
        gold_cost=45,
        materials={"wolf_fang": 2, "fiber": 1},
        description="A necklace of wolf fangs that enhances critical strikes.",
    ),
    # --- Bandit-material recipes (Desert) ---
    Recipe(
        recipe_id="craft_desert_bow",
        output_item="desert_bow",
        gold_cost=75,
        materials={"raw_gem": 1, "fiber": 2},
        description="A composite bow with gem-tipped arrows. Precise and deadly.",
    ),
    # --- Undead-material recipes (Swamp) ---
    Recipe(
        recipe_id="craft_bone_shield",
        output_item="bone_shield",
        gold_cost=65,
        materials={"bone_shard": 3, "dark_moss": 1},
        description="A shield of fused bones. Sturdy and HP-boosting.",
    ),
    Recipe(
        recipe_id="craft_spectral_blade",
        output_item="spectral_blade",
        gold_cost=180,
        materials={"ectoplasm": 2, "enchanted_dust": 1},
        description="A ghostly blade that strikes with ethereal precision.",
    ),
    # --- Orc-material recipes (Mountain) ---
    Recipe(
        recipe_id="craft_mountain_plate",
        output_item="mountain_plate",
        gold_cost=160,
        materials={"stone_block": 3, "iron_ore": 2},
        description="Massive stone-reinforced plate armor. Extremely heavy but durable.",
    ),
    # --- Harvestable-material recipes ---
    Recipe(
        recipe_id="craft_herbal_remedy",
        output_item="herbal_remedy",
        gold_cost=15,
        materials={"herb": 3, "glowing_mushroom": 1},
        description="A natural healing draught brewed from forest herbs and mushrooms.",
    ),
]

RECIPE_MAP: dict[str, Recipe] = {r.recipe_id: r for r in RECIPES}


def can_craft(recipe: Recipe, gold: int, inventory_items: list[str]) -> bool:
    """Check if the hero has enough gold and materials to craft."""
    if gold < recipe.gold_cost:
        return False
    for mat_id, qty in recipe.materials.items():
        if inventory_items.count(mat_id) < qty:
            return False
    return True


# ---------------------------------------------------------------------------
# Guild intel
# ---------------------------------------------------------------------------

# Material drop hints the guild provides
MATERIAL_HINTS: dict[str, str] = {
    # Goblin drops
    "wood": "Dropped by basic goblins. Also harvestable from Timber nodes in forests.",
    "leather": "Skinned from goblins, scouts, and wolves.",
    "iron_ore": "Found on goblin warriors, orcs, and in camp raids. Harvestable in deserts, swamps, and mountains.",
    "steel_bar": "Rare drop from goblin warriors and orc warriors.",
    "enchanted_dust": "Harvested from elite goblins, liches, and orc warlords. Crystal Nodes in mountains also yield it.",
    # Wolf drops (Forest)
    "wolf_pelt": "Skinned from wolves in forest regions. Common from all wolf types.",
    "wolf_fang": "Dropped by dire wolves and alpha wolves in forests.",
    # Bandit drops (Desert)
    "fiber": "Gathered from bandits in desert regions. Also harvestable from Cactus Fiber nodes.",
    "raw_gem": "Found on bandit archers and chiefs in desert regions. Gem Deposits also yield them.",
    # Undead drops (Swamp)
    "bone_shard": "Collected from skeletons and zombies in swamp regions.",
    "ectoplasm": "Extracted from zombies and liches in swamp regions. Rare and valuable.",
    "dark_moss": "Found in swamp regions. Dropped by skeletons or harvested from Dark Moss Patches.",
    "glowing_mushroom": "Grows in swamp regions. Dropped by zombies or harvested from Mushroom Groves.",
    # Orc drops (Mountain)
    "stone_block": "Mined from orcs in mountain regions. Also harvestable from Granite Quarries.",
    # Harvestable
    "herb": "Grows in forest regions. Harvestable from Herb Patch nodes.",
}


def get_sell_value_for_item(t: ItemTemplate) -> int:
    """Calculate sell value for display purposes."""
    if t.sell_value > 0:
        return t.sell_value
    if t.gold_value > 0:
        return t.gold_value
    return SELL_PRICES.get(t.rarity, 3)
