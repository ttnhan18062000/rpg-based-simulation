"""Item, Equipment, and Inventory system for the RPG engine."""

from __future__ import annotations

# Re-export core registry components
from src.core.item_registry import ITEM_REGISTRY, ItemTemplate

# Re-export core enums and factions used by items
from src.core.enums import EnemyTier, ItemType, Rarity
from src.core.faction import Faction

# Re-export moved models for backwards compatibility
from src.core.models import Inventory, HomeStorage, TreasureChest


# ---------------------------------------------------------------------------
# Power calculation
# ---------------------------------------------------------------------------

def _item_power(t: ItemTemplate) -> int:
    """Internal helper for calculating relative item strength."""
    return (t.atk_bonus + t.def_bonus + t.spd_bonus + t.max_hp_bonus + 
            t.matk_bonus + t.mdef_bonus + int(t.crit_rate_bonus * 50) + 
            int(t.evasion_bonus * 50) + (t.luck_bonus or 0))

def item_power(item_id: str) -> int:
    """Calculate power of an item from the registry."""
    from src.core.item_registry import ITEM_REGISTRY
    t = ITEM_REGISTRY.get(item_id)
    return _item_power(t) if t else 0


# ---------------------------------------------------------------------------
# Generation & Evolution Constants
# ---------------------------------------------------------------------------

TIER_KIND_NAMES = {
    EnemyTier.BASIC: "basic",
    EnemyTier.SCOUT: "scout",
    EnemyTier.WARRIOR: "warrior",
    EnemyTier.ELITE: "elite",
}

RACE_TIER_KINDS = {
    "goblin": {
        EnemyTier.BASIC: "goblin",
        EnemyTier.SCOUT: "goblin_scout",
        EnemyTier.WARRIOR: "goblin_warrior",
        EnemyTier.ELITE: "goblin_elite",
    },
    "wolf": {
        EnemyTier.BASIC: "wolf",
        EnemyTier.SCOUT: "dire_wolf",
        EnemyTier.WARRIOR: "alpha_wolf",
        EnemyTier.ELITE: "warg",
    },
    "bandit": {
        EnemyTier.BASIC: "bandit",
        EnemyTier.SCOUT: "bandit_archer",
        EnemyTier.WARRIOR: "bandit_warrior",
        EnemyTier.ELITE: "bandit_chief",
    },
    "undead": {
        EnemyTier.BASIC: "skeleton",
        EnemyTier.SCOUT: "skeleton_mage",
        EnemyTier.WARRIOR: "lich",
        EnemyTier.ELITE: "wraith",
    },
    "orc": {
        EnemyTier.BASIC: "orc",
        EnemyTier.SCOUT: "orc_scout",
        EnemyTier.WARRIOR: "orc_warrior",
        EnemyTier.ELITE: "orc_warlord",
    },
}

RACE_STARTING_GEAR = {
    "goblin": {
        EnemyTier.BASIC: {"weapon": "wooden_club"},
        EnemyTier.SCOUT: {"weapon": "bandit_dagger"},
        EnemyTier.WARRIOR: {"weapon": "iron_sword"},
        EnemyTier.ELITE: {"weapon": "goblin_cleaver"},
    },
    "orc": {
        EnemyTier.BASIC: {"weapon": "iron_sword", "armor": "leather_vest"},
        EnemyTier.WARRIOR: {"weapon": "orc_axe", "armor": "chainmail"},
        EnemyTier.ELITE: {"weapon": "orc_shield", "armor": "plate_armor"},
    },
    "bandit": {
        EnemyTier.BASIC: {"weapon": "bandit_dagger"},
        EnemyTier.SCOUT: {"weapon": "bandit_bow"},
        EnemyTier.WARRIOR: {"weapon": "iron_sword"},
    },
    "undead": {
        EnemyTier.SCOUT: {"weapon": "wooden_staff"},
        EnemyTier.ELITE: {"weapon": "crystal_staff"},
    }
}

TIER_STARTING_GEAR = {
    EnemyTier.BASIC: {"weapon": "wooden_club"},
    EnemyTier.SCOUT: {"weapon": "bandit_dagger"},
    EnemyTier.WARRIOR: {"weapon": "iron_sword"},
    EnemyTier.ELITE: {"weapon": "apprentice_staff"},
}

RACE_STAT_MODS = {
    "hero": (1.0, 1.0, 0, 0, 0.05, 0.0, 0),
    "goblin": (0.8, 1.1, -1, 1, 0.04, 0.05, 1),
    "wolf": (0.9, 1.0, -2, 4, 0.10, 0.10, 0),
    "bandit": (1.0, 1.1, 0, 2, 0.07, 0.08, 2),
    "undead": (1.2, 0.9, 2, -2, 0.02, 0.10, 0),
    "orc": (1.5, 1.4, 3, -1, 0.05, 0.02, 1),
}


# ---------------------------------------------------------------------------
# Loot & Economy
# ---------------------------------------------------------------------------

LOOT_TABLES: dict[int, list[tuple[str, float]]] = {
    EnemyTier.BASIC: [("small_hp_potion", 0.4), ("iron_sword", 0.10)],
    EnemyTier.ELITE: [("large_hp_potion", 0.5), ("goblin_cleaver", 0.30)],
}

RACE_LOOT_TABLES = {
    "goblin": [("wood", 0.3), ("leather", 0.1), ("iron_ore", 0.05)],
    "wolf": [("wolf_pelt", 0.4), ("wolf_fang", 0.1)],
    "bandit": [("fiber", 0.3), ("raw_gem", 0.05)],
    "undead": [("bone_shard", 0.4), ("ectoplasm", 0.1)],
    "orc": [("stone_block", 0.4), ("silver_ingot", 0.1)],
}

TERRAIN_RACE: dict[int, str] = {
    1: "wolf",    # FOREST
    2: "bandit",  # DESERT
    3: "undead",  # SWAMP
    4: "orc",     # MOUNTAIN
}

HOUSE_UPGRADE_COSTS: dict[int, int] = {
    0: 200,
    1: 500,
}

CHEST_LOOT_TABLES: dict[int, list[tuple[str, float, int, int]]] = {
    1: [("iron_ore", 0.5, 1, 3), ("wood", 0.5, 2, 5)],
    2: [("silver_ingot", 0.3, 1, 2), ("mana_shard", 0.2, 1, 1)],
    3: [("gold_ingot", 0.1, 1, 1), ("phoenix_feather", 0.05, 1, 1)],
}

RACE_FACTION: dict[str, Faction] = {
    "hero": Faction.HERO_GUILD,
    "goblin": Faction.GOBLIN_HORDE,
    "wolf": Faction.WOLF_PACK,
    "bandit": Faction.BANDIT_CLAN,
    "undead": Faction.UNDEAD,
    "orc": Faction.ORC_TRIBE,
}

DIFFICULTY_DROP_MULTIPLIER = {1: 1.0, 2: 1.2, 3: 1.5, 4: 2.0}

DIFFICULTY_BONUS_LOOT = {
    3: [("enchanted_dust", 0.1)],
    4: [("calamity_essence", 0.05), ("calamity_remnant", 0.02)],
}
