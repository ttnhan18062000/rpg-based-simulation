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
# Item power utilities
# ---------------------------------------------------------------------------

def _item_power(template) -> int:
    """Calculate item power from a template's base stats."""
    return (
        getattr(template, 'atk_bonus', 0)
        + getattr(template, 'def_bonus', 0)
        + getattr(template, 'spd_bonus', 0)
        + getattr(template, 'hp_bonus', 0)
        + int(getattr(template, 'crit_bonus', 0.0) * 100)
        + getattr(template, 'matk_bonus', 0)
        + getattr(template, 'mdef_bonus', 0)
    )


def item_power(item_id: str) -> int:
    """Public wrapper — returns 0 if item not found."""
    t = ITEM_REGISTRY.get(item_id)
    return _item_power(t) if t else 0


# ---------------------------------------------------------------------------
# Power calculation
# ---------------------------------------------------------------------------

TERRAIN_RACE: dict[int, str] = {
    6: "wolf",    # Material.FOREST
    7: "bandit",  # Material.DESERT
    8: "undead",  # Material.SWAMP
    9: "orc",     # Material.MOUNTAIN
}

HOUSE_UPGRADE_COSTS: dict[int, int] = {
    0: 200,
    1: 500,
}

CHEST_LOOT_TABLES: dict[int, list[tuple[str, float, int, int]]] = {
    1: [("iron_ore", 0.5, 1, 3), ("wood", 0.5, 2, 5)],
    2: [("silver_ingot", 0.3, 1, 2), ("mana_shard", 0.2, 1, 1)],
    3: [("gold_ingot", 0.1, 1, 1), ("phoenix_feather", 0.05, 1, 1)],
    4: [
        ("calamity_essence", 0.15, 1, 2),
        ("calamity_remnant", 0.10, 1, 1),
        ("enchanted_dust", 0.25, 1, 3),
        ("phoenix_feather", 0.20, 1, 2),
        ("gold_ingot", 0.30, 2, 5),
        ("mana_shard", 0.35, 2, 4),
    ],
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

DIFFICULTY_BONUS_LOOT: dict[int, list[tuple[str, float]]] = {
    1: [],
    2: [("enchanted_dust", 0.03)],
    3: [("enchanted_dust", 0.1)],
    4: [("calamity_essence", 0.05), ("calamity_remnant", 0.02)],
}

# ---------------------------------------------------------------------------
# Backward-compatible shims for removed constants
# ---------------------------------------------------------------------------
# world_loop.py still imports these for the evolution system.
# They now compute from the SPAWN_CONFIGS registry.

def _build_race_tier_kinds() -> dict:
    """Build RACE_TIER_KINDS: {race: {tier_int: kind_string}}"""
    from src.core.spawn_config import SPAWN_CONFIGS
    result: dict[str, dict[int, str]] = {}
    for (race, tier), cfg in SPAWN_CONFIGS.items():
        result.setdefault(race, {})[int(tier)] = cfg.kind
    return result

def _build_tier_kind_names() -> dict:
    """Build TIER_KIND_NAMES: {tier_int: generic kind name}"""
    return {0: "goblin", 1: "goblin_scout", 2: "goblin_warrior", 3: "goblin_chief"}

def _build_race_starting_gear() -> dict:
    """Build RACE_STARTING_GEAR: {race: {tier: {slot: item_id}}}"""
    from src.core.spawn_config import SPAWN_CONFIGS
    result: dict[str, dict[int, dict[str, str]]] = {}
    for (race, tier), cfg in SPAWN_CONFIGS.items():
        if cfg.starting_gear:
            gear_dict: dict[str, str] = {}
            for item_id in cfg.starting_gear:
                # Infer slot from item name pattern
                if "sword" in item_id or "bow" in item_id or "staff" in item_id or "dagger" in item_id or "axe" in item_id or "mace" in item_id:
                    gear_dict["weapon"] = item_id
                elif "armor" in item_id or "vest" in item_id or "robe" in item_id or "mail" in item_id or "hide" in item_id:
                    gear_dict["armor"] = item_id
                else:
                    gear_dict.setdefault("accessory", item_id)
            result.setdefault(race, {})[int(tier)] = gear_dict
    return result

class _LazyDict(dict):
    """Dict that populates itself on first access."""
    def __init__(self, builder):
        super().__init__()
        self._builder = builder
        self._populated = False
    def _ensure(self):
        if not self._populated:
            self.update(self._builder())
            self._populated = True
    def __getitem__(self, key):
        self._ensure()
        return super().__getitem__(key)
    def get(self, key, default=None):
        self._ensure()
        return super().get(key, default)
    def __contains__(self, key):
        self._ensure()
        return super().__contains__(key)

RACE_TIER_KINDS = _LazyDict(_build_race_tier_kinds)
TIER_KIND_NAMES = _LazyDict(_build_tier_kind_names)
RACE_STARTING_GEAR = _LazyDict(_build_race_starting_gear)
TIER_STARTING_GEAR = _LazyDict(lambda: {
    1: {"weapon": "bronze_sword", "armor": "padded_vest"},
    2: {"weapon": "steel_sword", "armor": "chain_mail"},
    3: {"weapon": "mithril_blade", "armor": "plate_armor"},
})
