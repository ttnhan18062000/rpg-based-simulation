"""Item, Equipment, and Inventory system for the RPG engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.core.enums import ItemType, Rarity

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Item template
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ItemTemplate:
    """Immutable blueprint for an item.  Instances are referenced by item_id."""

    item_id: str
    name: str
    item_type: ItemType
    rarity: Rarity
    weight: float = 1.0
    # Equipment stat bonuses
    atk_bonus: int = 0
    def_bonus: int = 0
    spd_bonus: int = 0
    max_hp_bonus: int = 0
    crit_rate_bonus: float = 0.0
    evasion_bonus: float = 0.0
    luck_bonus: int = 0
    # Consumable effects
    heal_amount: int = 0
    # Gold value (for loot/treasure)
    gold_value: int = 0
    # Sell value (gold received when selling to shop; 0 = auto-calc from rarity)
    sell_value: int = 0


# ---------------------------------------------------------------------------
# Item registry — all item definitions live here
# ---------------------------------------------------------------------------

ITEM_REGISTRY: dict[str, ItemTemplate] = {}


def _reg(t: ItemTemplate) -> ItemTemplate:
    ITEM_REGISTRY[t.item_id] = t
    return t


# ---- Weapons ----
_reg(ItemTemplate("wooden_club",       "Wooden Club",         ItemType.WEAPON, Rarity.COMMON,   weight=2.0, atk_bonus=2))
_reg(ItemTemplate("iron_sword",        "Iron Sword",          ItemType.WEAPON, Rarity.COMMON,   weight=3.0, atk_bonus=4))
_reg(ItemTemplate("steel_sword",       "Steel Sword",         ItemType.WEAPON, Rarity.UNCOMMON, weight=3.0, atk_bonus=6, spd_bonus=1))
_reg(ItemTemplate("battle_axe",        "Battle Axe",          ItemType.WEAPON, Rarity.UNCOMMON, weight=4.0, atk_bonus=8, spd_bonus=-1))
_reg(ItemTemplate("enchanted_blade",   "Enchanted Blade",     ItemType.WEAPON, Rarity.RARE,     weight=2.5, atk_bonus=10, spd_bonus=2, crit_rate_bonus=0.05))
_reg(ItemTemplate("goblin_cleaver",    "Goblin Chief Cleaver",ItemType.WEAPON, Rarity.RARE,     weight=3.5, atk_bonus=12, crit_rate_bonus=0.10))

# ---- Armor ----
_reg(ItemTemplate("leather_vest",      "Leather Vest",        ItemType.ARMOR, Rarity.COMMON,   weight=3.0, def_bonus=2))
_reg(ItemTemplate("chainmail",         "Chainmail",           ItemType.ARMOR, Rarity.UNCOMMON, weight=5.0, def_bonus=4, spd_bonus=-1))
_reg(ItemTemplate("iron_plate",        "Iron Plate",          ItemType.ARMOR, Rarity.UNCOMMON, weight=6.0, def_bonus=6, spd_bonus=-2))
_reg(ItemTemplate("enchanted_robe",    "Enchanted Robe",      ItemType.ARMOR, Rarity.RARE,     weight=2.0, def_bonus=4, spd_bonus=2, evasion_bonus=0.05))
_reg(ItemTemplate("goblin_guard",      "Goblin Chief Guard",  ItemType.ARMOR, Rarity.RARE,     weight=4.0, def_bonus=8, evasion_bonus=0.05))

# ---- Accessories ----
_reg(ItemTemplate("lucky_charm",       "Lucky Charm",         ItemType.ACCESSORY, Rarity.COMMON,   weight=0.5, crit_rate_bonus=0.03, luck_bonus=3))
_reg(ItemTemplate("speed_ring",        "Speed Ring",          ItemType.ACCESSORY, Rarity.UNCOMMON, weight=0.3, spd_bonus=3))
_reg(ItemTemplate("evasion_amulet",    "Amulet of Evasion",   ItemType.ACCESSORY, Rarity.UNCOMMON, weight=0.5, evasion_bonus=0.08))
_reg(ItemTemplate("ring_of_power",     "Ring of Power",       ItemType.ACCESSORY, Rarity.RARE,     weight=0.3, atk_bonus=3, def_bonus=3))

# ---- Materials (original) ----
_reg(ItemTemplate("wood",              "Wood",                ItemType.MATERIAL, Rarity.COMMON,   weight=1.0, sell_value=5))
_reg(ItemTemplate("iron_ore",          "Iron Ore",            ItemType.MATERIAL, Rarity.UNCOMMON, weight=2.0, sell_value=10))
_reg(ItemTemplate("steel_bar",         "Steel Bar",           ItemType.MATERIAL, Rarity.UNCOMMON, weight=3.0, sell_value=15))
_reg(ItemTemplate("leather",           "Leather",             ItemType.MATERIAL, Rarity.COMMON,   weight=1.5, sell_value=8))
_reg(ItemTemplate("enchanted_dust",    "Enchanted Dust",      ItemType.MATERIAL, Rarity.RARE,     weight=0.5, sell_value=20))

# ---- Materials (harvestable resources) ----
_reg(ItemTemplate("herb",              "Herb",                ItemType.MATERIAL, Rarity.COMMON,   weight=0.3, sell_value=4))
_reg(ItemTemplate("wild_berries",      "Wild Berries",        ItemType.CONSUMABLE, Rarity.COMMON, weight=0.3, heal_amount=8))
_reg(ItemTemplate("raw_gem",           "Raw Gem",             ItemType.MATERIAL, Rarity.UNCOMMON, weight=0.5, sell_value=18))
_reg(ItemTemplate("fiber",             "Fiber",               ItemType.MATERIAL, Rarity.COMMON,   weight=0.5, sell_value=4))
_reg(ItemTemplate("glowing_mushroom",  "Glowing Mushroom",    ItemType.MATERIAL, Rarity.UNCOMMON, weight=0.3, sell_value=12))
_reg(ItemTemplate("dark_moss",         "Dark Moss",           ItemType.MATERIAL, Rarity.COMMON,   weight=0.3, sell_value=6))
_reg(ItemTemplate("stone_block",       "Stone Block",         ItemType.MATERIAL, Rarity.COMMON,   weight=4.0, sell_value=7))

# ---- Mob-specific drops ----
_reg(ItemTemplate("wolf_pelt",         "Wolf Pelt",           ItemType.MATERIAL, Rarity.COMMON,   weight=1.5, sell_value=10))
_reg(ItemTemplate("wolf_fang",         "Wolf Fang",           ItemType.MATERIAL, Rarity.UNCOMMON, weight=0.3, sell_value=14))
_reg(ItemTemplate("bandit_dagger",     "Bandit Dagger",       ItemType.WEAPON,   Rarity.COMMON,   weight=1.5, atk_bonus=3, spd_bonus=2))
_reg(ItemTemplate("bandit_bow",        "Bandit Bow",          ItemType.WEAPON,   Rarity.UNCOMMON, weight=2.0, atk_bonus=5, crit_rate_bonus=0.05))
_reg(ItemTemplate("bone_shard",        "Bone Shard",          ItemType.MATERIAL, Rarity.COMMON,   weight=0.5, sell_value=6))
_reg(ItemTemplate("ectoplasm",         "Ectoplasm",           ItemType.MATERIAL, Rarity.UNCOMMON, weight=0.3, sell_value=16))
_reg(ItemTemplate("orc_axe",           "Orc Axe",             ItemType.WEAPON,   Rarity.UNCOMMON, weight=4.0, atk_bonus=7, spd_bonus=-1))
_reg(ItemTemplate("orc_shield",        "Orc Shield",          ItemType.ARMOR,    Rarity.UNCOMMON, weight=5.0, def_bonus=5, spd_bonus=-1))

# ---- Crafted items from race-specific materials ----
_reg(ItemTemplate("wolf_cloak",        "Wolf Cloak",          ItemType.ARMOR,     Rarity.UNCOMMON, weight=2.5, def_bonus=3, spd_bonus=2, evasion_bonus=0.04))
_reg(ItemTemplate("fang_necklace",     "Fang Necklace",       ItemType.ACCESSORY, Rarity.UNCOMMON, weight=0.3, atk_bonus=2, crit_rate_bonus=0.08))
_reg(ItemTemplate("desert_bow",        "Desert Composite Bow",ItemType.WEAPON,    Rarity.UNCOMMON, weight=2.0, atk_bonus=6, spd_bonus=1, crit_rate_bonus=0.06))
_reg(ItemTemplate("bone_shield",       "Bone Shield",         ItemType.ARMOR,     Rarity.UNCOMMON, weight=4.0, def_bonus=5, max_hp_bonus=10))
_reg(ItemTemplate("spectral_blade",    "Spectral Blade",      ItemType.WEAPON,    Rarity.RARE,     weight=2.0, atk_bonus=9, crit_rate_bonus=0.08))
_reg(ItemTemplate("mountain_plate",    "Mountain Plate",      ItemType.ARMOR,     Rarity.RARE,     weight=7.0, def_bonus=7, spd_bonus=-2, max_hp_bonus=15))
_reg(ItemTemplate("herbal_remedy",     "Herbal Remedy",       ItemType.CONSUMABLE, Rarity.COMMON,  weight=0.5, heal_amount=25))

# ---- Consumables ----
_reg(ItemTemplate("small_hp_potion",   "Small Health Potion", ItemType.CONSUMABLE, Rarity.COMMON,   weight=0.5, heal_amount=15))
_reg(ItemTemplate("medium_hp_potion",  "Medium Health Potion",ItemType.CONSUMABLE, Rarity.UNCOMMON, weight=0.5, heal_amount=30))
_reg(ItemTemplate("large_hp_potion",   "Large Health Potion", ItemType.CONSUMABLE, Rarity.RARE,     weight=1.0, heal_amount=50))

# ---- Treasure / loot items ----
_reg(ItemTemplate("gold_pouch_s",      "Small Gold Pouch",    ItemType.CONSUMABLE, Rarity.COMMON,   weight=0.5, gold_value=10))
_reg(ItemTemplate("gold_pouch_m",      "Gold Pouch",          ItemType.CONSUMABLE, Rarity.UNCOMMON, weight=1.0, gold_value=25))
_reg(ItemTemplate("gold_pouch_l",      "Large Gold Pouch",    ItemType.CONSUMABLE, Rarity.RARE,     weight=1.5, gold_value=50))
_reg(ItemTemplate("camp_treasure",     "Camp Treasure Chest", ItemType.CONSUMABLE, Rarity.RARE,     weight=3.0, gold_value=100))


def get_item(item_id: str) -> ItemTemplate | None:
    return ITEM_REGISTRY.get(item_id)


# ---------------------------------------------------------------------------
# Inventory — mutable container held by each entity
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Inventory:
    """Mutable item container with slot and weight limits."""

    items: list[str] = field(default_factory=list)  # list of item_ids
    max_slots: int = 8
    max_weight: float = 20.0
    # Equipment slots (item_id or None)
    weapon: str | None = None
    armor: str | None = None
    accessory: str | None = None

    @property
    def current_weight(self) -> float:
        total = 0.0
        for iid in self.items:
            t = ITEM_REGISTRY.get(iid)
            if t:
                total += t.weight
        for slot_id in (self.weapon, self.armor, self.accessory):
            if slot_id:
                t = ITEM_REGISTRY.get(slot_id)
                if t:
                    total += t.weight
        return total

    @property
    def used_slots(self) -> int:
        return len(self.items)

    def can_add(self, item_id: str) -> bool:
        if self.used_slots >= self.max_slots:
            return False
        t = ITEM_REGISTRY.get(item_id)
        if t is None:
            return False
        return self.current_weight + t.weight <= self.max_weight

    def add_item(self, item_id: str) -> bool:
        if not self.can_add(item_id):
            return False
        self.items.append(item_id)
        return True

    def remove_item(self, item_id: str) -> bool:
        if item_id in self.items:
            self.items.remove(item_id)
            return True
        return False

    def has_consumable(self, item_id: str) -> bool:
        return item_id in self.items

    def count_item(self, item_id: str) -> int:
        return self.items.count(item_id)

    def equip(self, item_id: str) -> bool:
        """Equip an item from inventory into the appropriate slot."""
        t = ITEM_REGISTRY.get(item_id)
        if t is None or item_id not in self.items:
            return False
        if t.item_type == ItemType.WEAPON:
            if self.weapon:
                self.items.append(self.weapon)
            self.weapon = item_id
        elif t.item_type == ItemType.ARMOR:
            if self.armor:
                self.items.append(self.armor)
            self.armor = item_id
        elif t.item_type == ItemType.ACCESSORY:
            if self.accessory:
                self.items.append(self.accessory)
            self.accessory = item_id
        else:
            return False
        self.items.remove(item_id)
        return True

    def equipment_bonus(self, stat: str) -> int | float:
        """Sum a stat bonus across all equipped items."""
        total: int | float = 0
        for slot_id in (self.weapon, self.armor, self.accessory):
            if slot_id:
                t = ITEM_REGISTRY.get(slot_id)
                if t:
                    total += getattr(t, stat, 0)
        return total

    def get_all_item_ids(self) -> list[str]:
        """Return all item_ids (inventory + equipped) — used for loot drops."""
        result = list(self.items)
        if self.weapon:
            result.append(self.weapon)
        if self.armor:
            result.append(self.armor)
        if self.accessory:
            result.append(self.accessory)
        return result

    def copy(self) -> Inventory:
        return Inventory(
            items=list(self.items),
            max_slots=self.max_slots,
            max_weight=self.max_weight,
            weapon=self.weapon,
            armor=self.armor,
            accessory=self.accessory,
        )


# ---------------------------------------------------------------------------
# Loot tables — per enemy tier
# ---------------------------------------------------------------------------

# Maps EnemyTier int value -> list of (item_id, drop_chance)
from src.core.enums import EnemyTier

LOOT_TABLES: dict[int, list[tuple[str, float]]] = {
    EnemyTier.BASIC: [
        ("small_hp_potion", 0.4),
        ("gold_pouch_s", 0.3),
        ("wooden_club", 0.15),
        ("leather_vest", 0.10),
        ("wood", 0.30),
        ("leather", 0.20),
    ],
    EnemyTier.SCOUT: [
        ("small_hp_potion", 0.5),
        ("gold_pouch_s", 0.4),
        ("speed_ring", 0.10),
        ("lucky_charm", 0.10),
        ("leather", 0.30),
        ("wood", 0.20),
    ],
    EnemyTier.WARRIOR: [
        ("medium_hp_potion", 0.4),
        ("gold_pouch_m", 0.4),
        ("iron_sword", 0.20),
        ("chainmail", 0.15),
        ("steel_sword", 0.08),
        ("iron_ore", 0.35),
        ("steel_bar", 0.15),
    ],
    EnemyTier.ELITE: [
        ("large_hp_potion", 0.5),
        ("gold_pouch_l", 0.5),
        ("goblin_cleaver", 0.30),
        ("goblin_guard", 0.25),
        ("enchanted_blade", 0.15),
        ("enchanted_robe", 0.10),
        ("ring_of_power", 0.10),
        ("camp_treasure", 0.40),
        ("enchanted_dust", 0.25),
        ("iron_ore", 0.30),
    ],
}

# --- Race-specific loot tables (by kind prefix) ---
RACE_LOOT_TABLES: dict[str, list[tuple[str, float]]] = {
    "wolf": [
        ("wolf_pelt", 0.50),
        ("wolf_fang", 0.25),
        ("leather", 0.30),
        ("small_hp_potion", 0.20),
    ],
    "dire_wolf": [
        ("wolf_pelt", 0.60),
        ("wolf_fang", 0.40),
        ("leather", 0.40),
        ("medium_hp_potion", 0.25),
        ("gold_pouch_s", 0.20),
    ],
    "alpha_wolf": [
        ("wolf_pelt", 0.80),
        ("wolf_fang", 0.60),
        ("leather", 0.50),
        ("large_hp_potion", 0.30),
        ("gold_pouch_m", 0.40),
        ("enchanted_dust", 0.10),
    ],
    "bandit": [
        ("bandit_dagger", 0.30),
        ("gold_pouch_s", 0.50),
        ("small_hp_potion", 0.35),
        ("fiber", 0.20),
    ],
    "bandit_archer": [
        ("bandit_bow", 0.25),
        ("gold_pouch_s", 0.50),
        ("medium_hp_potion", 0.30),
        ("raw_gem", 0.15),
        ("fiber", 0.25),
    ],
    "bandit_chief": [
        ("bandit_bow", 0.40),
        ("gold_pouch_l", 0.50),
        ("large_hp_potion", 0.35),
        ("raw_gem", 0.35),
        ("camp_treasure", 0.30),
        ("enchanted_dust", 0.15),
    ],
    "skeleton": [
        ("bone_shard", 0.50),
        ("gold_pouch_s", 0.25),
        ("wooden_club", 0.20),
        ("dark_moss", 0.20),
    ],
    "zombie": [
        ("bone_shard", 0.40),
        ("ectoplasm", 0.30),
        ("gold_pouch_s", 0.30),
        ("medium_hp_potion", 0.20),
        ("glowing_mushroom", 0.20),
    ],
    "lich": [
        ("ectoplasm", 0.60),
        ("bone_shard", 0.50),
        ("enchanted_dust", 0.40),
        ("gold_pouch_l", 0.50),
        ("large_hp_potion", 0.40),
        ("camp_treasure", 0.25),
    ],
    "orc": [
        ("orc_axe", 0.15),
        ("gold_pouch_s", 0.35),
        ("iron_ore", 0.30),
        ("small_hp_potion", 0.30),
        ("stone_block", 0.20),
    ],
    "orc_warrior": [
        ("orc_axe", 0.25),
        ("orc_shield", 0.20),
        ("gold_pouch_m", 0.40),
        ("iron_ore", 0.40),
        ("steel_bar", 0.20),
        ("medium_hp_potion", 0.30),
    ],
    "orc_warlord": [
        ("orc_axe", 0.50),
        ("orc_shield", 0.40),
        ("gold_pouch_l", 0.50),
        ("steel_bar", 0.40),
        ("enchanted_dust", 0.25),
        ("camp_treasure", 0.35),
        ("large_hp_potion", 0.40),
    ],
}

# Default starting equipment per enemy tier
TIER_STARTING_GEAR: dict[int, dict[str, str | None]] = {
    EnemyTier.BASIC: {"weapon": "wooden_club", "armor": None, "accessory": None},
    EnemyTier.SCOUT: {"weapon": None, "armor": None, "accessory": "lucky_charm"},
    EnemyTier.WARRIOR: {"weapon": "iron_sword", "armor": "chainmail", "accessory": None},
    EnemyTier.ELITE: {"weapon": "goblin_cleaver", "armor": "goblin_guard", "accessory": "ring_of_power"},
}

# Maps enemy tier -> kind string for display
TIER_KIND_NAMES: dict[int, str] = {
    EnemyTier.BASIC: "goblin",
    EnemyTier.SCOUT: "goblin_scout",
    EnemyTier.WARRIOR: "goblin_warrior",
    EnemyTier.ELITE: "goblin_chief",
}

# Race-specific tier kind names (race -> {tier -> kind})
RACE_TIER_KINDS: dict[str, dict[int, str]] = {
    "wolf": {
        EnemyTier.BASIC: "wolf",
        EnemyTier.SCOUT: "wolf",
        EnemyTier.WARRIOR: "dire_wolf",
        EnemyTier.ELITE: "alpha_wolf",
    },
    "bandit": {
        EnemyTier.BASIC: "bandit",
        EnemyTier.SCOUT: "bandit_archer",
        EnemyTier.WARRIOR: "bandit_archer",
        EnemyTier.ELITE: "bandit_chief",
    },
    "undead": {
        EnemyTier.BASIC: "skeleton",
        EnemyTier.SCOUT: "skeleton",
        EnemyTier.WARRIOR: "zombie",
        EnemyTier.ELITE: "lich",
    },
    "orc": {
        EnemyTier.BASIC: "orc",
        EnemyTier.SCOUT: "orc",
        EnemyTier.WARRIOR: "orc_warrior",
        EnemyTier.ELITE: "orc_warlord",
    },
}

# Race-specific starting gear
RACE_STARTING_GEAR: dict[str, dict[int, dict[str, str | None]]] = {
    "wolf": {
        EnemyTier.BASIC:   {"weapon": None, "armor": None, "accessory": None},
        EnemyTier.SCOUT:   {"weapon": None, "armor": None, "accessory": None},
        EnemyTier.WARRIOR: {"weapon": None, "armor": None, "accessory": None},
        EnemyTier.ELITE:   {"weapon": None, "armor": None, "accessory": "speed_ring"},
    },
    "bandit": {
        EnemyTier.BASIC:   {"weapon": "bandit_dagger", "armor": None, "accessory": None},
        EnemyTier.SCOUT:   {"weapon": "bandit_bow", "armor": None, "accessory": None},
        EnemyTier.WARRIOR: {"weapon": "bandit_bow", "armor": "leather_vest", "accessory": None},
        EnemyTier.ELITE:   {"weapon": "bandit_bow", "armor": "chainmail", "accessory": "lucky_charm"},
    },
    "undead": {
        EnemyTier.BASIC:   {"weapon": "wooden_club", "armor": None, "accessory": None},
        EnemyTier.SCOUT:   {"weapon": "wooden_club", "armor": None, "accessory": None},
        EnemyTier.WARRIOR: {"weapon": "iron_sword", "armor": "leather_vest", "accessory": None},
        EnemyTier.ELITE:   {"weapon": "enchanted_blade", "armor": "enchanted_robe", "accessory": "ring_of_power"},
    },
    "orc": {
        EnemyTier.BASIC:   {"weapon": "orc_axe", "armor": None, "accessory": None},
        EnemyTier.SCOUT:   {"weapon": "orc_axe", "armor": None, "accessory": None},
        EnemyTier.WARRIOR: {"weapon": "orc_axe", "armor": "orc_shield", "accessory": None},
        EnemyTier.ELITE:   {"weapon": "orc_axe", "armor": "orc_shield", "accessory": "ring_of_power"},
    },
}

# Stat adjustments per race (hp_mult, atk_mult, def_mod, spd_mod, crit, evasion, luck)
RACE_STAT_MODS: dict[str, tuple[float, float, int, int, float, float, int]] = {
    "wolf":   (0.8,  1.1, -1, 3,  0.08, 0.06, 1),  # fast, fragile, high crit
    "bandit": (1.0,  1.0,  1, 1,  0.10, 0.04, 3),  # balanced, lucky
    "undead": (1.3,  0.9,  2, -2, 0.04, 0.00, 0),  # tanky, slow
    "orc":    (1.4,  1.2,  3, -1, 0.06, 0.02, 1),  # strong, tanky
}

# Map terrain Material -> race string
TERRAIN_RACE: dict[int, str] = {
    6: "wolf",    # Material.FOREST
    7: "bandit",  # Material.DESERT
    8: "undead",  # Material.SWAMP
    9: "orc",     # Material.MOUNTAIN
}

# Map race -> Faction
from src.core.faction import Faction
RACE_FACTION: dict[str, Faction] = {
    "wolf": Faction.WOLF_PACK,
    "bandit": Faction.BANDIT_CLAN,
    "undead": Faction.UNDEAD,
    "orc": Faction.ORC_TRIBE,
}
